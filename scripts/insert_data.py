import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from common.database import Database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def insert_test_data():
    """Inserta datos de prueba en la base de datos"""
    
    logger.info("Conectando a la base de datos...")
    db = Database()
    
    try:
        # Insertar empresa de prueba
        logger.info("Insertando empresa de prueba...")
        db.execute_query(
            "INSERT INTO empresas (razon_social, cuit, activa) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
            ("Empresa Test SA", "30-12345678-9", True),
            fetch=False
        )
        
        # Insertar empleados de prueba
        logger.info("Insertando empleados de prueba...")
        for i in range(1, 6):
            db.execute_query(
                """INSERT INTO empleados (empresa_id, convenio_id, cuil, nombre, apellido, legajo, cbu, activo)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (empresa_id, cuil) DO NOTHING""",
                (1, 1, f"20-3456789{i}-0", f"Empleado{i}", f"Apellido{i}", f"LEG00{i}", "0000003100012345678901", True),
                fetch=False
            )
        
        logger.info("Datos de prueba insertados correctamente")
        logger.info("")
        logger.info("Empresa: Empresa Test SA (CUIT: 30-12345678-9)")
        logger.info("Empleados: 5 empleados de prueba creados")
        logger.info("")
        logger.info("Ahora puedes iniciar el servidor y los workers")
        
    except Exception as e:
        logger.error(f"Error insertando datos: {e}")
        return False
    
    finally:
        db.close()
    
    return True


if __name__ == '__main__':
    logger.info("="*60)
    logger.info("INSERCION DE DATOS DE PRUEBA")
    logger.info("="*60)
    logger.info("")
    
    success = insert_test_data()
    
    if success:
        logger.info("")
        logger.info("="*60)
        logger.info("DATOS INSERTADOS EXITOSAMENTE")
        logger.info("="*60)
    else:
        logger.error("")
        logger.error("="*60)
        logger.error("ERROR AL INSERTAR DATOS")
        logger.error("="*60)
        sys.exit(1)