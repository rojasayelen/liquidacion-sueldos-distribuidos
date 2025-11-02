import sys
import os
import time
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cliente.cliente import Cliente
from common.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_insertar_datos_prueba():
    """Inserta datos de prueba en la BD"""
    logger.info("Insertando datos de prueba...")
    
    db = Database()
    
    # Insertar empresa
    db.execute_query(
        "INSERT INTO empresas (razon_social, cuit, activa) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
        ("Empresa Test SA", "30-12345678-9", True),
        fetch=False
    )
    
    # Insertar empleados
    for i in range(1, 6):
        db.execute_query(
            """INSERT INTO empleados (empresa_id, convenio_id, cuil, nombre, apellido, legajo, cbu, activo)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (empresa_id, cuil) DO NOTHING""",
            (1, 1, f"20-3456789{i}-0", f"Empleado{i}", f"Apellido{i}", f"LEG00{i}", "0000003100012345678901", True),
            fetch=False
        )
    
    db.close()
    logger.info("Datos de prueba insertados correctamente")


def test_liquidacion():
    """Test de liquidación de sueldo"""
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
    """Test de generación de reporte"""
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
    """Test de generación de archivo bancario"""
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
    """Test de cálculo de cargas sociales"""
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
    
    # Insertar datos de prueba
    test_insertar_datos_prueba()
    
    time.sleep(2)
    
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