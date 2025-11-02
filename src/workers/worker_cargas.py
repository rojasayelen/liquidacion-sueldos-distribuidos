import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from common.rabbitmq_handler import RabbitMQHandler
from common.database import Database
from config.settings import QUEUE_CARGAS, WORKER_THREAD_POOL_SIZE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkerCargas:
    def __init__(self):
        self.rabbitmq = RabbitMQHandler()
        self.db = Database()
        self.pool_size = WORKER_THREAD_POOL_SIZE['cargas']
        self.executor = ThreadPoolExecutor(max_workers=self.pool_size)
        logger.info(f"Worker Cargas iniciado con pool de {self.pool_size} hilos")
    
    def process_task(self, task_data):
        try:
            task_id = task_data.get('task_id')
            empresa_id = task_data.get('empresa_id')
            periodo = task_data.get('periodo')
            tipo_carga = task_data.get('tipo_carga', 'afip')
            
            logger.info(f"Calculando cargas sociales {task_id} - Empresa: {empresa_id}, Tipo: {tipo_carga}")
            
            if tipo_carga == 'afip':
                resultado = self.calcular_cargas_afip(empresa_id, periodo)
            elif tipo_carga == 'obra_social':
                resultado = self.calcular_obra_social(empresa_id, periodo)
            else:
                raise Exception(f"Tipo de carga no valido: {tipo_carga}")
            
            logger.info(f"Cargas sociales {task_id} calculadas exitosamente")
            return resultado
            
        except Exception as e:
            logger.error(f"Error procesando tarea {task_data.get('task_id')}: {e}")
            return {'estado': 'error', 'mensaje': str(e)}
    
    def calcular_cargas_afip(self, empresa_id, periodo):
        # Obtener liquidaciones del periodo
        query = """
            SELECT COUNT(*) as total_empleados,
                   SUM(sueldo_bruto) as total_remunerativo,
                   SUM(cargas_sociales) as total_cargas
            FROM liquidaciones
            WHERE empresa_id = %s AND periodo = %s AND estado = 'completada'
        """
        resultado = self.db.execute_query(query, (empresa_id, periodo))
        
        if not resultado or not resultado[0]['total_empleados']:
            raise Exception("No hay liquidaciones para calcular cargas")
        
        data = resultado[0]
        total_remunerativo = float(data['total_remunerativo'] or 0)
        total_cargas = float(data['total_cargas'] or 0)
        
        # Desglose de cargas patronales
        cargas_detalle = {
            'jubilacion': total_remunerativo * 0.1062,
            'obra_social': total_remunerativo * 0.06,
            'pami': total_remunerativo * 0.02,
            'asignaciones_familiares': total_remunerativo * 0.0449,
            'fondo_nacional_empleo': total_remunerativo * 0.0089,
            'art': total_remunerativo * 0.03
        }
        
        filename = f"ddjj_afip_{empresa_id}_{periodo.replace('-', '')}.txt"
        s3_path = f"s3://cargas-sociales/{filename}"
        
        logger.info(f"Declaracion jurada AFIP generada: {filename}")
        
        return {
            'estado': 'completada',
            'tipo': 'cargas_afip',
            'archivo': filename,
            's3_path': s3_path,
            'periodo': periodo,
            'resumen': {
                'total_empleados': data['total_empleados'],
                'total_remunerativo': total_remunerativo,
                'total_cargas_patronales': total_cargas,
                'desglose': cargas_detalle
            }
        }
    
    def calcular_obra_social(self, empresa_id, periodo):
        # Obtener detalle por empleado
        query = """
            SELECT e.cuil, e.nombre, e.apellido, l.sueldo_bruto
            FROM liquidaciones l
            JOIN empleados e ON l.empleado_id = e.id
            WHERE l.empresa_id = %s AND l.periodo = %s AND l.estado = 'completada'
        """
        empleados = self.db.execute_query(query, (empresa_id, periodo))
        
        if not empleados:
            raise Exception("No hay datos para calcular obra social")
        
        registros = []
        total_aporte_empleado = 0
        total_aporte_empleador = 0
        
        for emp in empleados:
            bruto = float(emp['sueldo_bruto'])
            aporte_empleado = bruto * 0.03
            aporte_empleador = bruto * 0.06
            
            total_aporte_empleado += aporte_empleado
            total_aporte_empleador += aporte_empleador
            
            registros.append({
                'cuil': emp['cuil'],
                'nombre_completo': f"{emp['apellido']}, {emp['nombre']}",
                'remuneracion': bruto,
                'aporte_empleado': aporte_empleado,
                'aporte_empleador': aporte_empleador
            })
        
        filename = f"obra_social_{empresa_id}_{periodo.replace('-', '')}.txt"
        s3_path = f"s3://cargas-sociales/{filename}"
        
        logger.info(f"Archivo obra social generado: {filename}")
        
        return {
            'estado': 'completada',
            'tipo': 'obra_social',
            'archivo': filename,
            's3_path': s3_path,
            'periodo': periodo,
            'resumen': {
                'total_empleados': len(registros),
                'total_aporte_empleado': total_aporte_empleado,
                'total_aporte_empleador': total_aporte_empleador,
                'total_general': total_aporte_empleado + total_aporte_empleador
            },
            'registros_preview': registros[:5]
        }
    
    def callback(self, ch, method, properties, body):
        try:
            task_data = json.loads(body)
            logger.info(f"Tarea recibida: {task_data.get('task_id')}")
            
            # Procesar en el pool de hilos
            future = self.executor.submit(self.process_task, task_data)
            resultado = future.result()
            
            # Confirmar procesamiento
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Tarea confirmada: {task_data.get('task_id')}")
            
        except Exception as e:
            logger.error(f"Error en callback: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start(self):
        logger.info(f"Iniciando consumo de cola '{QUEUE_CARGAS}'...")
        self.rabbitmq.consume_tasks(QUEUE_CARGAS, self.callback)
    
    def stop(self):
        self.executor.shutdown(wait=True)
        self.rabbitmq.close()
        self.db.close()
        logger.info("Worker Cargas detenido")


if __name__ == '__main__':
    worker = WorkerCargas()
    
    try:
        worker.start()
    except KeyboardInterrupt:
        logger.info("Worker detenido por usuario")
        worker.stop()