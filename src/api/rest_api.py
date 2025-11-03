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
            'procesado_por': data.get('procesado_por', 'Web/Mobile')
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


@app.route('/api/liquidaciones', methods=['GET'])
def obtener_liquidaciones():
    """Obtiene las últimas liquidaciones procesadas"""
    try:
        from common.database import Database
        db = Database()
        
        query = """
            SELECT l.id, l.periodo, l.estado, l.sueldo_bruto, l.sueldo_neto, 
                   l.cargas_sociales, l.procesado_por, l.created_at,
                   e.nombre, e.apellido, emp.razon_social
            FROM liquidaciones l
            JOIN empleados e ON l.empleado_id = e.id
            JOIN empresas emp ON l.empresa_id = emp.id
            ORDER BY l.created_at DESC
            LIMIT 50
        """
        
        liquidaciones = db.execute_query(query)
        db.close()
        
        if liquidaciones:
            result = []
            for liq in liquidaciones:
                result.append({
                    'id': liq['id'],
                    'empleado': f"{liq['nombre']} {liq['apellido']}",
                    'empresa': liq['razon_social'],
                    'periodo': liq['periodo'],
                    'estado': liq['estado'],
                    'sueldo_bruto': float(liq['sueldo_bruto']) if liq['sueldo_bruto'] else 0,
                    'sueldo_neto': float(liq['sueldo_neto']) if liq['sueldo_neto'] else 0,
                    'cargas_sociales': float(liq['cargas_sociales']) if liq['cargas_sociales'] else 0,
                    'procesado_por': liq['procesado_por'],
                    'fecha': liq['created_at'].isoformat() if liq['created_at'] else None
                })
            return jsonify({'liquidaciones': result}), 200
        else:
            return jsonify({'liquidaciones': []}), 200
            
    except Exception as e:
        logger.error(f"Error obteniendo liquidaciones: {e}")
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@app.route('/api/tareas', methods=['GET'])
def obtener_tareas():
    """Obtiene el historial de tareas"""
    try:
        from common.database import Database
        db = Database()
        
        query = """
            SELECT id, tipo, estado, created_at, updated_at
            FROM tareas
            ORDER BY created_at DESC
            LIMIT 100
        """
        
        tareas = db.execute_query(query)
        db.close()
        
        if tareas:
            result = []
            for tarea in tareas:
                result.append({
                    'id': tarea['id'],
                    'tipo': tarea['tipo'],
                    'estado': tarea['estado'],
                    'created_at': tarea['created_at'].isoformat() if tarea['created_at'] else None,
                    'updated_at': tarea['updated_at'].isoformat() if tarea['updated_at'] else None
                })
            return jsonify({'tareas': result}), 200
        else:
            return jsonify({'tareas': []}), 200
            
    except Exception as e:
        logger.error(f"Error obteniendo tareas: {e}")
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500


@app.route('/api/estadisticas', methods=['GET'])
def obtener_estadisticas():
    """Obtiene estadísticas generales del sistema"""
    try:
        from common.database import Database
        db = Database()
        
        # Total de liquidaciones
        query_liq = "SELECT COUNT(*) as total FROM liquidaciones WHERE estado = 'completada'"
        result_liq = db.execute_query(query_liq)
        total_liquidaciones = result_liq[0]['total'] if result_liq else 0
        
        # Liquidaciones hoy
        query_hoy = """
            SELECT COUNT(*) as total FROM liquidaciones 
            WHERE DATE(created_at) = CURRENT_DATE AND estado = 'completada'
        """
        result_hoy = db.execute_query(query_hoy)
        liquidaciones_hoy = result_hoy[0]['total'] if result_hoy else 0
        
        # Total procesado
        query_total = """
            SELECT SUM(sueldo_neto) as total FROM liquidaciones 
            WHERE estado = 'completada'
        """
        result_total = db.execute_query(query_total)
        total_procesado = float(result_total[0]['total']) if result_total and result_total[0]['total'] else 0
        
        # Empleados activos
        query_emp = "SELECT COUNT(*) as total FROM empleados WHERE activo = true"
        result_emp = db.execute_query(query_emp)
        empleados_activos = result_emp[0]['total'] if result_emp else 0
        
        db.close()
        
        return jsonify({
            'total_liquidaciones': total_liquidaciones,
            'liquidaciones_hoy': liquidaciones_hoy,
            'total_procesado': total_procesado,
            'empleados_activos': empleados_activos
        }), 200
            
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
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