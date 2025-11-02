import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        try:
            self.connection = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            logger.info(f"Conectado a PostgreSQL: {DB_NAME}")
        except Exception as e:
            logger.error(f"Error conectando a PostgreSQL: {e}")
            raise
    
    def execute_query(self, query, params=None, fetch=True):
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            
            if fetch:
                result = cursor.fetchall()
                cursor.close()
                return result
            else:
                self.connection.commit()
                cursor.close()
                return True
        except Exception as e:
            logger.error(f"Error ejecutando query: {e}")
            self.connection.rollback()
            return None
    
    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("Conexion a PostgreSQL cerrada")