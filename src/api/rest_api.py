import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, jsonify
from flask_cors import CORS
import socket
import json
import logging
from config.settings import SOCKET_HOST, SOCKET_PORT_1, SOCKET_BUFFER_SIZE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


def enviar_tarea_socket(tarea, host='localhost', port=SOCKET_PORT_1):
    """Envía tarea al servidor socket y retorna respuesta"""
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        
        mensaje = json.dumps(tarea)
        client_socket.send(mensaje.encode('utf-8'))
        
        respuesta = client_socket.recv(SOCKET_BUFFER_SIZE).decode('utf-8')
        respuesta_json = json.loads(respuesta)
        
        client_socket.close()
        
        return respuesta_json
        
    except Exception as e:
        logger.error(f"Error enviando tarea: {e}")
        return {'status': 'error', 'mensaje': str(e)}


@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check"""
    return jsonify({'status': 'ok', 'service': 'API REST Liquidacion'}), 200


@app.route('/api/liquidacion', methods=['POST'])
def liquidacion():
    """Endpoint para enviar tarea de liquidación"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'mensaje': 'No se recibieron datos'}), 400
        
        tarea = {
            'tipo': 'liquidacion',
            'empresa_id': data.get('empresa_id'),
            'empleado_id': data.get('empleado_id'),
            'periodo': data.get('periodo'),
            'procesado_por': data.get('procesado_por', 'Web/Mobile'),
            'conceptos': data.get('conceptos', [])
        }
        
        respuesta = enviar_tarea_socket(tarea)
        
        if respuesta['status'] == 'aceptada':
            return jsonify(respuesta), 200
        else:
            return jsonify(respuesta), 500
            
    except Exception as e:
        logger.error(f"Error en endpoint liquidacion: {e}")
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@app.route('/api/reporte', methods=['POST'])
def reporte():
    """Endpoint para generar reportes"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'mensaje': 'No se recibieron datos'}), 400
        
        tarea = {
            'tipo': 'reporte',
            'tipo_reporte': data.get('tipo_reporte'),
            'liquidacion_id': data.get('liquidacion_id'),
            'empresa_id': data.get('empresa_id'),
            'periodo': data.get('periodo')
        }
        
        respuesta = enviar_tarea_socket(tarea)
        
        if respuesta['status'] == 'aceptada':
            return jsonify(respuesta), 200
        else:
            return jsonify(respuesta), 500
            
    except Exception as e:
        logger.error(f"Error en endpoint reporte: {e}")
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@app.route('/api/archivo-bancario', methods=['POST'])
def archivo_bancario():
    """Endpoint para generar archivos bancarios"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'mensaje': 'No se recibieron datos'}), 400
        
        tarea = {
            'tipo': 'archivo_bancario',
            'empresa_id': data.get('empresa_id'),
            'periodo': data.get('periodo'),
            'banco': data.get('banco', 'generico')
        }
        
        respuesta = enviar_tarea_socket(tarea)
        
        if respuesta['status'] == 'aceptada':
            return jsonify(respuesta), 200
        else:
            return jsonify(respuesta), 500
            
    except Exception as e:
        logger.error(f"Error en endpoint archivo bancario: {e}")
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@app.route('/api/cargas-sociales', methods=['POST'])
def cargas_sociales():
    """Endpoint para calcular cargas sociales"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'mensaje': 'No se recibieron datos'}), 400
        
        tarea = {
            'tipo': 'carga_social',
            'tipo_carga': data.get('tipo_carga', 'afip'),
            'empresa_id': data.get('empresa_id'),
            'periodo': data.get('periodo')
        }
        
        respuesta = enviar_tarea_socket(tarea)
        
        if respuesta['status'] == 'aceptada':
            return jsonify(respuesta), 200
        else:
            return jsonify(respuesta), 500
            
    except Exception as e:
        logger.error(f"Error en endpoint cargas sociales: {e}")
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@app.route('/api/tarea', methods=['POST'])
def tarea_generica():
    """Endpoint genérico para cualquier tipo de tarea"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'mensaje': 'No se recibieron datos'}), 400
        
        if 'tipo' not in data:
            return jsonify({'status': 'error', 'mensaje': 'Falta campo tipo'}), 400
        
        respuesta = enviar_tarea_socket(data)
        
        if respuesta['status'] == 'aceptada':
            return jsonify(respuesta), 200
        else:
            return jsonify(respuesta), 500
            
    except Exception as e:
        logger.error(f"Error en endpoint genérico: {e}")
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


if __name__ == '__main__':
    logger.info("Iniciando API REST en puerto 5000...")
    logger.info("Endpoints disponibles:")
    logger.info("  GET  /health")
    logger.info("  POST /api/liquidacion")
    logger.info("  POST /api/reporte")
    logger.info("  POST /api/archivo-bancario")
    logger.info("  POST /api/cargas-sociales")
    logger.info("  POST /api/tarea (genérico)")
    logger.info("")
    logger.info("Conectando a Socket Server en localhost:9001")
    
    app.run(host='0.0.0.0', port=5000, debug=True)