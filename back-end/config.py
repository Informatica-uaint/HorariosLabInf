import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
env_path = Path(__file__).parent / '.env.example'
load_dotenv(dotenv_path=env_path)

class Config:
    """Configuración base de la aplicación"""

    # JWT
    JWT_SECRET = os.getenv('JWT_SECRET')

    # Base de datos
    DB_HOST = os.getenv('MYSQL_HOST')
    DB_USER = os.getenv('MYSQL_USER')
    DB_PASSWORD = os.getenv('MYSQL_PASSWORD')
    DB_NAME = os.getenv('MYSQL_DB')
    DB_PORT = int(os.getenv('MYSQL_PORT', 3306))
    DB_CHARSET = os.getenv('DB_CHARSET', 'utf8mb4')

    # Servidor
    SERVER_URL = 'https://acceso.informaticauaint.com'

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Timezone
    TIMEZONE = 'America/Santiago'
    
    # Días de la semana
    DIAS_SEMANA = {
        'Monday': 'lunes',
        'Tuesday': 'martes',
        'Wednesday': 'miércoles',
        'Thursday': 'jueves',
        'Friday': 'viernes',
        'Saturday': 'sábado',
        'Sunday': 'domingo'
    }
    
    # Traducción inversa
    DIAS_TRADUCCION = {
        'monday': 'lunes',
        'tuesday': 'martes',
        'wednesday': 'miércoles',
        'thursday': 'jueves',
        'friday': 'viernes',
        'saturday': 'sábado',
        'sunday': 'domingo'
    }
