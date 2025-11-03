import json
import logging
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from common.rabbitmq_handler import RabbitMQHandler
from common.database import Database
from config.settings import QUEUE_REPORTES, WORKER_THREAD_POOL_SIZE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkerReportes:
    def __init__(self):
        self.rabbitmq = RabbitMQHandler()
        self.db = Database()
        self.pool_size = WORKER_THREAD_POOL_SIZE['reportes']
        self.executor = ThreadPoolExecutor(max_workers=self.pool_size)
        logger.info(f"Worker Reportes iniciado con pool de {self.pool_size} hilos")
    
    def process_task(self, task_data):
        try:
            task_id = task_data.get('task_id')
            tipo_reporte = task_data.get('tipo_reporte')
            liquidacion_id = task_data.get('liquidacion_id')
            
            logger.info(f"Generando reporte {task_id} - Tipo: {tipo_reporte}")
            
            if tipo_reporte == 'recibo_sueldo':
                resultado = self.generar_recibo(liquidacion_id)
            elif tipo_reporte == 'reporte_sindical':
                resultado = self.generar_reporte_sindical(task_data)
            else:
                raise Exception(f"Tipo de reporte no valido: {tipo_reporte}")
            
            logger.info(f"Reporte {task_id} generado exitosamente")
            return resultado
            
        except Exception as e:
            logger.error(f"Error procesando tarea {task_data.get('task_id')}: {e}")
            return {'estado': 'error', 'mensaje': str(e)}
    
    def generar_recibo(self, liquidacion_id):
        # Obtener datos de liquidacion
        query = """
            SELECT l.*, e.nombre, e.apellido, e.cuil, emp.razon_social
            FROM liquidaciones l
            JOIN empleados e ON l.empleado_id = e.id
            JOIN empresas emp ON l.empresa_id = emp.id
            WHERE l.id = %s
        """
        liquidacion = self.db.execute_query(query, (liquidacion_id,))
        
        if not liquidacion:
            raise Exception(f"Liquidacion {liquidacion_id} no encontrada")
        
        data = liquidacion[0]
        
        # Simular generacion de PDF
        filename = f"recibo_{data['cuil']}_{data['periodo']}.pdf"
        s3_path = f"s3://recibos/{filename}"
        
        # Simular contenido del PDF
        contenido = {
            'empleado': f"{data['nombre']} {data['apellido']}",
            'cuil': data['cuil'],
            'empresa': data['razon_social'],
            'periodo': data['periodo'],
            'bruto': float(data['sueldo_bruto']),
            'neto': float(data['sueldo_neto']),
            'fecha_generacion': datetime.now().isoformat()
        }
        
        logger.info(f"PDF generado: {filename}")
        
        return {
            'estado': 'completada',
            'tipo': 'recibo_sueldo',
            'archivo': filename,
            's3_path': s3_path,
            'datos': contenido
        }
    
    def generar_reporte_sindical(self, task_data):
        empresa_id = task_data.get('empresa_id')
        periodo = task_data.get('periodo')
        
        # Obtener liquidaciones del periodo
        query = """
            SELECT COUNT(*) as total_empleados, 
                   SUM(sueldo_bruto) as total_bruto,
                   SUM(cargas_sociales) as total_cargas
            FROM liquidaciones
            WHERE empresa_id = %s AND periodo = %s
        """
        resultado = self.db.execute_query(query, (empresa_id, periodo))
        
        if not resultado:
            raise Exception("No hay datos para el periodo")
        
        data = resultado[0]
        
        filename = f"reporte_sindical_{empresa_id}_{periodo}.pdf"
        s3_path = f"s3://reportes/{filename}"
        
        logger.info(f"Reporte sindical generado: {filename}")
        
        return {
            'estado': 'completada',
            'tipo': 'reporte_sindical',
            'archivo': filename,
            's3_path': s3_path,
            'resumen': {
                'total_empleados': data['total_empleados'],
                'total_bruto': float(data['total_bruto'] or 0),
                'total_cargas': float(data['total_cargas'] or 0),
                'periodo': periodo
            }
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
        logger.info(f"Iniciando consumo de cola '{QUEUE_REPORTES}'...")
        self.rabbitmq.consume_tasks(QUEUE_REPORTES, self.callback)
    
    def stop(self):
        self.executor.shutdown(wait=True)
        self.rabbitmq.close()
        self.db.close()
        logger.info("Worker Reportes detenido")


if __name__ == '__main__':
    worker = WorkerReportes()
    
    try:
        worker.start()
    except KeyboardInterrupt:
        logger.info("Worker detenido por usuario")
        worker.stop()