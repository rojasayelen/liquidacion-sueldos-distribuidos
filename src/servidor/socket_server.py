import socket
import threading
import json
import logging
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from datetime import datetime
from common.rabbitmq_handler import RabbitMQHandler
from config.settings import (
    SOCKET_HOST,
    SOCKET_PORT_1,
    SOCKET_BUFFER_SIZE,
    SOCKET_MAX_CONNECTIONS,
    QUEUE_LIQUIDACION,
    QUEUE_REPORTES,
    QUEUE_ARCHIVOS,
    QUEUE_CARGAS
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SocketServer:
    def __init__(self, port):
        self.host = SOCKET_HOST
        self.port = port
        self.socket = None
        self.rabbitmq = RabbitMQHandler()
        self.running = False
        
        # Mapeo de tipo de tarea a cola
        self.queue_mapping = {
            'liquidacion': QUEUE_LIQUIDACION,
            'reporte': QUEUE_REPORTES,
            'archivo_bancario': QUEUE_ARCHIVOS,
            'carga_social': QUEUE_CARGAS
        }
    
    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(SOCKET_MAX_CONNECTIONS)
            self.running = True
            
            logger.info(f"Servidor Socket iniciado en {self.host}:{self.port}")
            logger.info(f"Esperando conexiones (max: {SOCKET_MAX_CONNECTIONS})...")
            
            # Declarar todas las colas
            for queue in self.queue_mapping.values():
                self.rabbitmq.declare_queue(queue)
            
            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    logger.info(f"Cliente conectado desde {address}")
                    
                    # Crear hilo para manejar el cliente
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.start()
                    
                except Exception as e:
                    logger.error(f"Error aceptando conexion: {e}")
        
        except Exception as e:
            logger.error(f"Error iniciando servidor: {e}")
        finally:
            self.stop()
    
    def handle_client(self, client_socket, address):
        try:
            # Recibir datos del cliente
            data = client_socket.recv(SOCKET_BUFFER_SIZE).decode('utf-8')
            
            if not data:
                logger.warning(f"Cliente {address} envio datos vacios")
                return
            
            # Parsear JSON
            task_request = json.loads(data)
            logger.info(f"Tarea recibida de {address}: {task_request.get('tipo', 'desconocido')}")
            
            # Validar y enriquecer tarea
            task = self.prepare_task(task_request, address)
            
            # Publicar en RabbitMQ
            queue_name = self.queue_mapping.get(task['tipo'])
            
            if queue_name:
                success = self.rabbitmq.publish_task(queue_name, task)
                
                if success:
                    response = {
                        'status': 'aceptada',
                        'task_id': task['task_id'],
                        'cola': queue_name,
                        'mensaje': 'Tarea encolada correctamente'
                    }
                else:
                    response = {
                        'status': 'error',
                        'mensaje': 'Error al encolar tarea'
                    }
            else:
                response = {
                    'status': 'error',
                    'mensaje': f"Tipo de tarea no valido: {task['tipo']}"
                }
            
            # Enviar respuesta al cliente
            client_socket.send(json.dumps(response).encode('utf-8'))
            logger.info(f"Respuesta enviada a {address}: {response['status']}")
            
        except json.JSONDecodeError:
            logger.error(f"Error: datos no son JSON valido desde {address}")
            error_response = {'status': 'error', 'mensaje': 'Formato JSON invalido'}
            client_socket.send(json.dumps(error_response).encode('utf-8'))
        
        except Exception as e:
            logger.error(f"Error manejando cliente {address}: {e}")
        
        finally:
            client_socket.close()
    
    def prepare_task(self, task_request, address):
        task = task_request.copy()
        task['task_id'] = f"{task['tipo']}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        task['timestamp'] = datetime.now().isoformat()
        task['client_address'] = str(address)
        return task
    
    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()
        self.rabbitmq.close()
        logger.info(f"Servidor en puerto {self.port} detenido")


if __name__ == '__main__':
    import sys
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else SOCKET_PORT_1
    server = SocketServer(port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Servidor detenido por usuario")
        server.stop()