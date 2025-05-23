import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """Configuración base de la aplicación"""
    
    # JWT
    JWT_SECRET = os.getenv('JWT_SECRET')
    
    # Base de datos
    DB_HOST = os.getenv('DB_HOST')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_CHARSET = os.getenv('DB_CHARSET', 'utf8mb4')
    
    # Servidor
    SERVER_URL = 'https://acceso.informaticauaint.com'
    
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