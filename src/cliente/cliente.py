import socket
import json
import logging
import time
from config.settings import SOCKET_HOST, SOCKET_PORT_1, SOCKET_BUFFER_SIZE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Cliente:
    def __init__(self, host=SOCKET_HOST, port=SOCKET_PORT_1):
        self.host = host
        self.port = port
    
    def enviar_tarea(self, tarea):
        try:
            # Crear socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.host, self.port))
            logger.info(f"Conectado al servidor {self.host}:{self.port}")
            
            # Enviar tarea
            mensaje = json.dumps(tarea)
            client_socket.send(mensaje.encode('utf-8'))
            logger.info(f"Tarea enviada: {tarea['tipo']}")
            
            # Recibir respuesta
            respuesta = client_socket.recv(SOCKET_BUFFER_SIZE).decode('utf-8')
            respuesta_json = json.loads(respuesta)
            
            logger.info(f"Respuesta recibida: {respuesta_json['status']}")
            
            if respuesta_json['status'] == 'aceptada':
                logger.info(f"Task ID: {respuesta_json['task_id']}")
                logger.info(f"Cola: {respuesta_json['cola']}")
            
            client_socket.close()
            return respuesta_json
            
        except Exception as e:
            logger.error(f"Error al enviar tarea: {e}")
            return None


def ejemplo_liquidacion():
    cliente = Cliente()
    
    tarea = {
        'tipo': 'liquidacion',
        'empresa_id': 1,
        'empleado_id': 1,
        'periodo': '2025-10',
        'procesado_por': 'Contador Juan Perez',
        'conceptos': [
            {'codigo': '00001', 'nombre': 'Sueldo Basico', 'tipo': 'remunerativo', 'monto': 500000},
            {'codigo': '000100', 'nombre': 'Antiguedad', 'tipo': 'remunerativo', 'monto': 50000},
            {'codigo': '000200', 'nombre': 'Presentismo', 'tipo': 'remunerativo', 'monto': 25000}
        ]
    }
    
    return cliente.enviar_tarea(tarea)


def ejemplo_reporte_recibo():
    cliente = Cliente()
    
    tarea = {
        'tipo': 'reporte',
        'tipo_reporte': 'recibo_sueldo',
        'liquidacion_id': 1
    }
    
    return cliente.enviar_tarea(tarea)


def ejemplo_reporte_sindical():
    cliente = Cliente()
    
    tarea = {
        'tipo': 'reporte',
        'tipo_reporte': 'reporte_sindical',
        'empresa_id': 1,
        'periodo': '2025-10'
    }
    
    return cliente.enviar_tarea(tarea)


def ejemplo_archivo_bancario():
    cliente = Cliente()
    
    tarea = {
        'tipo': 'archivo_bancario',
        'empresa_id': 1,
        'periodo': '2025-10',
        'banco': 'nacion'
    }
    
    return cliente.enviar_tarea(tarea)


def ejemplo_cargas_afip():
    cliente = Cliente()
    
    tarea = {
        'tipo': 'carga_social',
        'tipo_carga': 'afip',
        'empresa_id': 1,
        'periodo': '2025-10'
    }
    
    return cliente.enviar_tarea(tarea)


def ejemplo_cargas_obra_social():
    cliente = Cliente()
    
    tarea = {
        'tipo': 'carga_social',
        'tipo_carga': 'obra_social',
        'empresa_id': 1,
        'periodo': '2025-10'
    }
    
    return cliente.enviar_tarea(tarea)


def enviar_multiples_liquidaciones():
    """Simula varios contadores liquidando simultaneamente"""
    cliente = Cliente()
    
    logger.info("Enviando multiples liquidaciones...")
    
    for i in range(1, 6):
        tarea = {
            'tipo': 'liquidacion',
            'empresa_id': 1,
            'empleado_id': i,
            'periodo': '2025-10',
            'procesado_por': f'Contador {i}',
            'conceptos': [
                {'codigo': '00001', 'nombre': 'Sueldo Basico', 'tipo': 'remunerativo', 'monto': 450000 + (i * 10000)},
                {'codigo': '000100', 'nombre': 'Antiguedad', 'tipo': 'remunerativo', 'monto': 40000 + (i * 5000)}
            ]
        }
        
        cliente.enviar_tarea(tarea)
        time.sleep(0.5)


if __name__ == '__main__':
    print("\n=== SISTEMA DE LIQUIDACION DE SUELDOS - CLIENTE ===\n")
    print("Ejemplos disponibles:")
    print("1. Liquidacion de sueldo")
    print("2. Reporte recibo de sueldo")
    print("3. Reporte sindical")
    print("4. Archivo bancario")
    print("5. Cargas sociales AFIP")
    print("6. Cargas sociales Obra Social")
    print("7. Enviar multiples liquidaciones")
    
    opcion = input("\nSeleccione una opcion (1-7): ")
    
    if opcion == '1':
        ejemplo_liquidacion()
    elif opcion == '2':
        ejemplo_reporte_recibo()
    elif opcion == '3':
        ejemplo_reporte_sindical()
    elif opcion == '4':
        ejemplo_archivo_bancario()
    elif opcion == '5':
        ejemplo_cargas_afip()
    elif opcion == '6':
        ejemplo_cargas_obra_social()
    elif opcion == '7':
        enviar_multiples_liquidaciones()
    else:
        print("Opcion invalida")