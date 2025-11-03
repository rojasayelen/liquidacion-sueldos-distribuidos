import json
import logging
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from common.rabbitmq_handler import RabbitMQHandler
from common.database import Database
from config.settings import QUEUE_ARCHIVOS, WORKER_THREAD_POOL_SIZE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkerArchivos:
    def __init__(self):
        self.rabbitmq = RabbitMQHandler()
        self.db = Database()
        self.pool_size = WORKER_THREAD_POOL_SIZE['archivos']
        self.executor = ThreadPoolExecutor(max_workers=self.pool_size)
        logger.info(f"Worker Archivos iniciado con pool de {self.pool_size} hilos")
    
    def process_task(self, task_data):
        try:
            task_id = task_data.get('task_id')
            empresa_id = task_data.get('empresa_id')
            periodo = task_data.get('periodo')
            banco = task_data.get('banco', 'generico')
            
            logger.info(f"Generando archivo bancario {task_id} - Empresa: {empresa_id}, Banco: {banco}")
            
            resultado = self.generar_archivo_bancario(empresa_id, periodo, banco)
            
            logger.info(f"Archivo bancario {task_id} generado exitosamente")
            return resultado
            
        except Exception as e:
            logger.error(f"Error procesando tarea {task_data.get('task_id')}: {e}")
            return {'estado': 'error', 'mensaje': str(e)}
    
    def generar_archivo_bancario(self, empresa_id, periodo, banco):
        # Obtener liquidaciones del periodo
        query = """
            SELECT l.id, e.cuil, e.cbu, e.nombre, e.apellido, l.sueldo_neto, emp.cuit
            FROM liquidaciones l
            JOIN empleados e ON l.empleado_id = e.id
            JOIN empresas emp ON l.empresa_id = emp.id
            WHERE l.empresa_id = %s AND l.periodo = %s AND l.estado = 'completada'
            ORDER BY e.apellido, e.nombre
        """
        liquidaciones = self.db.execute_query(query, (empresa_id, periodo))
        
        if not liquidaciones:
            raise Exception(f"No hay liquidaciones para generar archivo")
        
        # Generar contenido del archivo
        lineas = []
        total_registros = 0
        total_importe = 0
        
        # Header del archivo
        empresa_cuit = liquidaciones[0]['cuit']
        fecha_proceso = datetime.now().strftime('%Y%m%d')
        
        header = f"0{empresa_cuit}{fecha_proceso}{periodo.replace('-', '')}"
        lineas.append(header)
        
        # Registros de empleados
        for liq in liquidaciones:
            total_registros += 1
            total_importe += float(liq['sueldo_neto'])
            
            # Formato: CUIL|CBU|APELLIDO|NOMBRE|IMPORTE
            cbu = liq['cbu'] or '0' * 22
            linea = f"1{liq['cuil']}{cbu}{liq['apellido'][:20]:20}{liq['nombre'][:20]:20}{int(liq['sueldo_neto'] * 100):015d}"
            lineas.append(linea)
        
        # Footer del archivo
        footer = f"9{total_registros:08d}{int(total_importe * 100):018d}"
        lineas.append(footer)
        
        # Generar nombre de archivo
        filename = f"pago_{banco}_{empresa_id}_{periodo.replace('-', '')}.txt"
        s3_path = f"s3://archivos-bancarios/{filename}"
        
        # Simular guardado del archivo
        contenido = "\n".join(lineas)
        
        logger.info(f"Archivo generado: {filename} - {total_registros} registros, Total: ${total_importe:.2f}")
        
        return {
            'estado': 'completada',
            'tipo': 'archivo_bancario',
            'archivo': filename,
            's3_path': s3_path,
            'banco': banco,
            'resumen': {
                'total_registros': total_registros,
                'total_importe': float(total_importe),
                'periodo': periodo
            },
            'contenido_preview': lineas[:5]
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
        logger.info(f"Iniciando consumo de cola '{QUEUE_ARCHIVOS}'...")
        self.rabbitmq.consume_tasks(QUEUE_ARCHIVOS, self.callback)
    
    def stop(self):
        self.executor.shutdown(wait=True)
        self.rabbitmq.close()
        self.db.close()
        logger.info("Worker Archivos detenido")


if __name__ == '__main__':
    worker = WorkerArchivos()
    
    try:
        worker.start()
    except KeyboardInterrupt:
        logger.info("Worker detenido por usuario")
        worker.stop()