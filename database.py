import pymysql
from config import Config

def get_db_config():
    """Obtiene la configuración de la base de datos"""
    return {
        'host': Config.DB_HOST,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'database': Config.DB_NAME,
        'port': Config.DB_PORT,
        'charset': Config.DB_CHARSET,
        'cursorclass': pymysql.cursors.DictCursor
    }

def get_connection():
    """Crea y retorna una nueva conexión a la base de datos"""
    return pymysql.connect(**get_db_config())