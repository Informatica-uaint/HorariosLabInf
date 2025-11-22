import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno (.env si existe, si no .env.example)
base_path = Path(__file__).parent
env_path = base_path / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv(dotenv_path=base_path / '.env.example')

class Config:
    """Configuración base de la aplicación"""

    # JWT
    JWT_SECRET = os.getenv('JWT_SECRET')
    READER_QR_SECRET = os.getenv('READER_QR_SECRET')
    READER_STATION_ID = os.getenv('READER_STATION_ID', 'lector-web')

    # Control de puerta (ESPHOME)
    DOOR_HOST = os.getenv('DOOR_HOST')
    DOOR_PORT = int(os.getenv('DOOR_PORT', 6053))
    DOOR_DEVICE_NAME = os.getenv('DOOR_DEVICE_NAME', 'arturito')
    DOOR_API_KEY = os.getenv('DOOR_API_KEY')

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
