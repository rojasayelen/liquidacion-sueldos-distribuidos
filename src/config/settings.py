import os
from dotenv import load_dotenv

load_dotenv()

# Configuracion RabbitMQ
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'admin')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'admin123')

# Colas de RabbitMQ
QUEUE_LIQUIDACION = 'liquidacion'
QUEUE_REPORTES = 'reportes'
QUEUE_ARCHIVOS = 'archivos_bancarios'
QUEUE_CARGAS = 'cargas_sociales'
QUEUE_RESULTS = 'results'

# Configuracion PostgreSQL
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'liquidacion_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'postgres123')

# Configuracion Servidores Socket
SOCKET_HOST = os.getenv('SOCKET_HOST', '0.0.0.0')
SOCKET_PORT_1 = int(os.getenv('SOCKET_PORT_1', 9001))
SOCKET_PORT_2 = int(os.getenv('SOCKET_PORT_2', 9002))
SOCKET_PORT_3 = int(os.getenv('SOCKET_PORT_3', 9003))
SOCKET_BUFFER_SIZE = 4096
SOCKET_MAX_CONNECTIONS = 10

# Pool de hilos por Worker
WORKER_THREAD_POOL_SIZE = {
    'liquidacion': 5,
    'reportes': 5,
    'archivos': 3,
    'cargas': 3
}

# Timeout de tareas (segundos)
TASK_TIMEOUT = 300