import pytz
from datetime import datetime, time, timedelta, date
from config import Config

# Timezone configurado
TIMEZONE = pytz.timezone(Config.TIMEZONE)

def get_current_datetime():
    """Obtiene la fecha y hora actual en la zona horaria configurada"""
    return datetime.now(pytz.utc).astimezone(TIMEZONE)

def format_hora(hora_value):
    """Formatea un valor de hora a string HH:MM:SS"""
    if isinstance(hora_value, time):
        return hora_value.strftime("%H:%M:%S")
    elif isinstance(hora_value, timedelta):
        secs = int(hora_value.total_seconds())
        hh, rem = divmod(secs, 3600)
        mm, ss = divmod(rem, 60)
        return f"{hh:02d}:{mm:02d}:{ss:02d}"
    elif isinstance(hora_value, str):
        return hora_value
    else:
        return str(hora_value)

def convert_to_time(hora_value):
    """Convierte diversos formatos de hora a datetime.time"""
    if isinstance(hora_value, time):
        return hora_value
    elif isinstance(hora_value, timedelta):
        secs = int(hora_value.total_seconds())
        hh, rem = divmod(secs, 3600)
        mm, ss = divmod(rem, 60)
        return time(hh, mm, ss)
    elif isinstance(hora_value, str):
        try:
            return datetime.strptime(hora_value, "%H:%M:%S").time()
        except ValueError:
            try:
                return datetime.strptime(hora_value, "%H:%M").time()
            except ValueError:
                return time(0, 0, 0)
    else:
        try:
            return datetime.strptime(str(hora_value), "%H:%M:%S").time()
        except:
            return time(0, 0, 0)

def get_week_dates():
    """Obtiene las fechas de inicio y fin de la semana actual"""
    now = get_current_datetime()
    start_of_week = now - timedelta(days=now.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week