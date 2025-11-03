import sys
import os
import time
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cliente.cliente import Cliente
from common.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_liquidacion():
    """Test de liquidacion de sueldo"""
    logger.info("\n=== TEST 1: LIQUIDACION DE SUELDO ===")
    
    cliente = Cliente()
    
    tarea = {
        'tipo': 'liquidacion',
        'empresa_id': 1,
        'empleado_id': 1,
        'periodo': '2025-10',
        'procesado_por': 'Test Automatizado',
        'conceptos': [
            {'codigo': '00001', 'nombre': 'Sueldo Basico', 'tipo': 'remunerativo', 'monto': 500000},
            {'codigo': '000100', 'nombre': 'Antiguedad', 'tipo': 'remunerativo', 'monto': 50000}
        ]
    }
    
    respuesta = cliente.enviar_tarea(tarea)
    
    if respuesta and respuesta['status'] == 'aceptada':
        logger.info("TEST LIQUIDACION: PASS")
        return True
    else:
        logger.error("TEST LIQUIDACION: FAIL")
        return False


def test_reporte():
    """Test de generacion de reporte"""
    logger.info("\n=== TEST 2: GENERACION DE REPORTE ===")
    
    time.sleep(2)
    
    cliente = Cliente()
    
    tarea = {
        'tipo': 'reporte',
        'tipo_reporte': 'recibo_sueldo',
        'liquidacion_id': 1
    }
    
    respuesta = cliente.enviar_tarea(tarea)
    
    if respuesta and respuesta['status'] == 'aceptada':
        logger.info("TEST REPORTE: PASS")
        return True
    else:
        logger.error("TEST REPORTE: FAIL")
        return False


def test_archivo_bancario():
    """Test de generacion de archivo bancario"""
    logger.info("\n=== TEST 3: ARCHIVO BANCARIO ===")
    
    time.sleep(2)
    
    cliente = Cliente()
    
    tarea = {
        'tipo': 'archivo_bancario',
        'empresa_id': 1,
        'periodo': '2025-10',
        'banco': 'nacion'
    }
    
    respuesta = cliente.enviar_tarea(tarea)
    
    if respuesta and respuesta['status'] == 'aceptada':
        logger.info("TEST ARCHIVO BANCARIO: PASS")
        return True
    else:
        logger.error("TEST ARCHIVO BANCARIO: FAIL")
        return False


def test_cargas_sociales():
    """Test de calculo de cargas sociales"""
    logger.info("\n=== TEST 4: CARGAS SOCIALES ===")
    
    time.sleep(2)
    
    cliente = Cliente()
    
    tarea = {
        'tipo': 'carga_social',
        'tipo_carga': 'afip',
        'empresa_id': 1,
        'periodo': '2025-10'
    }
    
    respuesta = cliente.enviar_tarea(tarea)
    
    if respuesta and respuesta['status'] == 'aceptada':
        logger.info("TEST CARGAS SOCIALES: PASS")
        return True
    else:
        logger.error("TEST CARGAS SOCIALES: FAIL")
        return False


def test_carga_concurrente():
    """Test de multiples tareas simultaneas"""
    logger.info("\n=== TEST 5: CARGA CONCURRENTE ===")
    
    cliente = Cliente()
    exitosos = 0
    
    for i in range(2, 6):
        tarea = {
            'tipo': 'liquidacion',
            'empresa_id': 1,
            'empleado_id': i,
            'periodo': '2025-10',
            'procesado_por': f'Test Concurrente {i}',
            'conceptos': [
                {'codigo': '00001', 'nombre': 'Sueldo Basico', 'tipo': 'remunerativo', 'monto': 450000 + (i * 10000)}
            ]
        }
        
        respuesta = cliente.enviar_tarea(tarea)
        if respuesta and respuesta['status'] == 'aceptada':
            exitosos += 1
        
        time.sleep(0.3)
    
    if exitosos == 4:
        logger.info("TEST CARGA CONCURRENTE: PASS")
        return True
    else:
        logger.error(f"TEST CARGA CONCURRENTE: FAIL (exitosos: {exitosos}/4)")
        return False


def verificar_resultados():
    """Verifica resultados en la base de datos"""
    logger.info("\n=== VERIFICACION DE RESULTADOS EN BD ===")
    
    db = Database()
    
    # Contar liquidaciones
    result = db.execute_query("SELECT COUNT(*) as total FROM liquidaciones WHERE estado = 'completada'")
    total_liquidaciones = result[0]['total'] if result else 0
    
    logger.info(f"Total de liquidaciones completadas: {total_liquidaciones}")
    
    db.close()
    
    if total_liquidaciones >= 5:
        logger.info("VERIFICACION BD: PASS")
        return True
    else:
        logger.error("VERIFICACION BD: FAIL")
        return False


if __name__ == '__main__':
    logger.info("\n" + "="*60)
    logger.info("SUITE DE TESTS DE INTEGRACION")
    logger.info("="*60)
    logger.info("\nNOTA: Asegurese de haber ejecutado scripts/insert_data.py primero")
    logger.info("y de tener el servidor y los workers corriendo.\n")
    
    # Ejecutar tests
    resultados = []
    resultados.append(test_liquidacion())
    resultados.append(test_reporte())
    resultados.append(test_archivo_bancario())
    resultados.append(test_cargas_sociales())
    resultados.append(test_carga_concurrente())
    
    # Esperar procesamiento
    logger.info("\nEsperando que los workers procesen las tareas...")
    time.sleep(5)
    
    # Verificar resultados
    resultados.append(verificar_resultados())
    
    # Resumen
    logger.info("\n" + "="*60)
    logger.info("RESUMEN DE TESTS")
    logger.info("="*60)
    total = len(resultados)
    exitosos = sum(resultados)
    logger.info(f"Tests exitosos: {exitosos}/{total}")
    
    if exitosos == total:
        logger.info("TODOS LOS TESTS PASARON")
    else:
        logger.error("ALGUNOS TESTS FALLARON")