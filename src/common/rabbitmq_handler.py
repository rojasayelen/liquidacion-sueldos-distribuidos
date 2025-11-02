import pika
import json
import logging
from config.settings import (
    RABBITMQ_HOST, 
    RABBITMQ_PORT, 
    RABBITMQ_USER, 
    RABBITMQ_PASS
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RabbitMQHandler:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connect()
    
    def connect(self):
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            logger.info(f"Conectado a RabbitMQ en {RABBITMQ_HOST}:{RABBITMQ_PORT}")
        except Exception as e:
            logger.error(f"Error conectando a RabbitMQ: {e}")
            raise
    
    def declare_queue(self, queue_name):
        self.channel.queue_declare(queue=queue_name, durable=True)
        logger.info(f"Cola '{queue_name}' declarada")
    
    def publish_task(self, queue_name, task_data):
        try:
            message = json.dumps(task_data)
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            logger.info(f"Tarea publicada en cola '{queue_name}': {task_data.get('task_id', 'N/A')}")
            return True
        except Exception as e:
            logger.error(f"Error publicando tarea: {e}")
            return False
    
    def consume_tasks(self, queue_name, callback):
        self.declare_queue(queue_name)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=False
        )
        logger.info(f"Esperando tareas en cola '{queue_name}'...")
        self.channel.start_consuming()
    
    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Conexion a RabbitMQ cerrada")