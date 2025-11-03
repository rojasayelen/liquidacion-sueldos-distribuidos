import json
import logging
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from concurrent.futures import ThreadPoolExecutor
from common.rabbitmq_handler import RabbitMQHandler
from common.database import Database
from config.settings import QUEUE_LIQUIDACION, WORKER_THREAD_POOL_SIZE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkerLiquidacion:
    def __init__(self):
        self.rabbitmq = RabbitMQHandler()
        self.db = Database()
        self.pool_size = WORKER_THREAD_POOL_SIZE['liquidacion']
        self.executor = ThreadPoolExecutor(max_workers=self.pool_size)
        logger.info(f"Worker Liquidacion iniciado con pool de {self.pool_size} hilos")
    
    def process_task(self, task_data):
        try:
            task_id = task_data.get('task_id')
            empresa_id = task_data.get('empresa_id')
            empleado_id = task_data.get('empleado_id')
            periodo = task_data.get('periodo')
            conceptos = task_data.get('conceptos', [])
            
            logger.info(f"Procesando liquidacion {task_id} - Empresa: {empresa_id}, Empleado: {empleado_id}")
            
            # Obtener datos del empleado
            empleado = self.get_empleado(empleado_id)
            if not empleado:
                raise Exception(f"Empleado {empleado_id} no encontrado")
            
            # Calcular liquidacion
            sueldo_bruto = self.calcular_bruto(conceptos)
            deducciones = self.calcular_deducciones(sueldo_bruto)
            sueldo_neto = sueldo_bruto - deducciones
            cargas_sociales = self.calcular_cargas_sociales(sueldo_bruto)
            
            # Guardar en BD
            liquidacion_id = self.guardar_liquidacion(
                empresa_id, empleado_id, periodo,
                sueldo_bruto, sueldo_neto, cargas_sociales,
                task_data.get('procesado_por', 'sistema')
            )
            
            resultado = {
                'liquidacion_id': liquidacion_id,
                'empleado': f"{empleado['nombre']} {empleado['apellido']}",
                'sueldo_bruto': float(sueldo_bruto),
                'deducciones': float(deducciones),
                'sueldo_neto': float(sueldo_neto),
                'cargas_sociales': float(cargas_sociales),
                'estado': 'completada'
            }
            
            logger.info(f"Liquidacion {task_id} procesada exitosamente - Neto: ${sueldo_neto:.2f}")
            return resultado
            
        except Exception as e:
            logger.error(f"Error procesando tarea {task_data.get('task_id')}: {e}")
            return {'estado': 'error', 'mensaje': str(e)}
    
    def get_empleado(self, empleado_id):
        query = "SELECT * FROM empleados WHERE id = %s"
        result = self.db.execute_query(query, (empleado_id,))
        return result[0] if result else None
    
    def calcular_bruto(self, conceptos):
        total = 0
        for concepto in conceptos:
            if concepto.get('tipo') == 'remunerativo':
                total += concepto.get('monto', 0)
        return total
    
    def calcular_deducciones(self, sueldo_bruto):
        jubilacion = sueldo_bruto * 0.11
        ley19032 = sueldo_bruto * 0.03
        obra_social = sueldo_bruto * 0.03
        return jubilacion + ley19032 + obra_social
    
    def calcular_cargas_sociales(self, sueldo_bruto):
        # Simplificado: 23% aproximado de cargas patronales
        return sueldo_bruto * 0.23
    
    def guardar_liquidacion(self, empresa_id, empleado_id, periodo, bruto, neto, cargas, procesado_por):
        query = """
            INSERT INTO liquidaciones 
            (empresa_id, empleado_id, periodo, estado, sueldo_bruto, sueldo_neto, cargas_sociales, procesado_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self.db.execute_query(
            query,
            (empresa_id, empleado_id, periodo, 'completada', bruto, neto, cargas, procesado_por),
            fetch=False
        )
        return result
    
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
        logger.info(f"Iniciando consumo de cola '{QUEUE_LIQUIDACION}'...")
        self.rabbitmq.consume_tasks(QUEUE_LIQUIDACION, self.callback)
    
    def stop(self):
        self.executor.shutdown(wait=True)
        self.rabbitmq.close()
        self.db.close()
        logger.info("Worker Liquidacion detenido")


if __name__ == '__main__':
    worker = WorkerLiquidacion()
    
    try:
        worker.start()
    except KeyboardInterrupt:
        logger.info("Worker detenido por usuario")
        worker.stop()