# utils/helpers.py - Funciones de ayuda y utilidades
from flask import jsonify
from datetime import datetime, date, time
import logging
import traceback

def format_response(data, message=None, status='success'):
    """
    Formatea respuestas de la API de manera consistente
    
    Args:
        data: Datos a retornar
        message: Mensaje opcional
        status: Estado de la respuesta
    
    Returns:
        Flask response object
    """
    response = {
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'data': data
    }
    
    if message:
        response['message'] = message
    
    return jsonify(response)

def handle_error(error, message="Error interno del servidor", status_code=500):
    """
    Maneja errores de manera consistente
    
    Args:
        error: Excepción capturada
        message: Mensaje de error personalizado
        status_code: Código de estado HTTP
    
    Returns:
        Flask response object con error
    """
    error_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Log del error completo
    logging.error(f"Error ID {error_id}: {str(error)}")
    logging.error(f"Traceback: {traceback.format_exc()}")
    
    # En desarrollo, incluir más detalles del error
    import os
    if os.getenv('FLASK_ENV') == 'development':
        error_detail = str(error)
    else:
        error_detail = "Error interno del servidor"
    
    response = {
        'status': 'error',
        'timestamp': datetime.now().isoformat(),
        'error': {
            'message': message,
            'detail': error_detail,
            'error_id': error_id
        }
    }
    
    return jsonify(response), status_code

def serialize_datetime(obj):
    """
    Serializa objetos datetime para JSON
    
    Args:
        obj: Objeto a serializar
    
    Returns:
        String ISO format o el objeto original
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, time):
        return obj.strftime('%H:%M:%S')
    
    return obj

def paginate_query_results(results, page=1, per_page=50):
    """
    Pagina resultados de consulta
    
    Args:
        results: Lista de resultados
        page: Número de página (empezando en 1)
        per_page: Resultados por página
    
    Returns:
        Dict con resultados paginados y metadata
    """
    total = len(results)
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_results = results[start:end]
    
    return {
        'data': paginated_results,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'has_next': end < total,
            'has_prev': start > 0
        }
    }

def validate_pagination_params(request):
    """
    Valida y extrae parámetros de paginación
    
    Args:
        request: Flask request object
    
    Returns:
        Dict con parámetros validados
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        # Validar rangos
        page = max(1, page)
        per_page = max(1, min(per_page, 100))  # Máximo 100 por página
        
        return {'page': page, 'per_page': per_page}
    
    except ValueError:
        return {'page': 1, 'per_page': 50}

def format_database_error(error):
    """
    Formatea errores de base de datos para respuestas user-friendly
    
    Args:
        error: MySQL error object
    
    Returns:
        String con mensaje de error formateado
    """
    error_msg = str(error)
    
    # Errores comunes de MySQL
    if "Duplicate entry" in error_msg:
        if "email" in error_msg:
            return "Ya existe un registro con este email"
        return "Ya existe un registro con estos datos"
    
    elif "cannot be null" in error_msg.lower():
        return "Faltan campos requeridos"
    
    elif "foreign key constraint" in error_msg.lower():
        return "No se puede eliminar el registro porque está siendo usado"
    
    elif "connection" in error_msg.lower():
        return "Error de conexión con la base de datos"
    
    elif "access denied" in error_msg.lower():
        return "Error de autenticación con la base de datos"
    
    else:
        return "Error en la base de datos"

def clean_email(email):
    """
    Limpia y normaliza emails
    
    Args:
        email: Email a limpiar
    
    Returns:
        Email limpio y normalizado
    """
    if not email:
        return ''
    
    return str(email).strip().lower()

def generate_response_id():
    """
    Genera un ID único para rastrear respuestas
    
    Returns:
        String con ID único
    """
    return datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]

def safe_int(value, default=0):
    """
    Convierte valor a int de manera segura
    
    Args:
        value: Valor a convertir
        default: Valor por defecto si falla la conversión
    
    Returns:
        Int convertido o valor por defecto
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_bool(value, default=False):
    """
    Convierte valor a bool de manera segura
    
    Args:
        value: Valor a convertir
        default: Valor por defecto
    
    Returns:
        Bool convertido o valor por defecto
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ['true', '1', 'yes', 'on']
    
    if isinstance(value, int):
        return bool(value)
    
    return default

def format_student_name(nombre, apellido):
    """
    Formatea nombre completo de estudiante
    
    Args:
        nombre: Nombre del estudiante
        apellido: Apellido del estudiante
    
    Returns:
        String con nombre formateado
    """
    if not nombre and not apellido:
        return "Sin nombre"
    
    if not apellido:
        return str(nombre).strip()
    
    if not nombre:
        return str(apellido).strip()
    
    return f"{str(nombre).strip()} {str(apellido).strip()}"

def get_day_name_spanish(date_obj):
    """
    Obtiene el nombre del día en español
    
    Args:
        date_obj: Objeto date de Python
    
    Returns:
        String con nombre del día en español
    """
    days = {
        'Monday': 'Lunes',
        'Tuesday': 'Martes',
        'Wednesday': 'Miércoles',
        'Thursday': 'Jueves',
        'Friday': 'Viernes',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    
    english_day = date_obj.strftime('%A')
    return days.get(english_day, english_day)

def log_api_call(request, response_data=None, error=None):
    """
    Registra llamadas a la API para auditoría
    
    Args:
        request: Flask request object
        response_data: Datos de respuesta (opcional)
        error: Error si lo hubo (opcional)
    """
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'method': request.method,
        'endpoint': request.endpoint,
        'url': request.url,
        'remote_addr': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
    }
    
    if error:
        log_data['error'] = str(error)
        logging.warning(f"API Call with error: {log_data}")
    else:
        logging.info(f"API Call: {log_data}")

def create_success_response(data, message=None):
    """
    Crea respuesta de éxito estándar
    
    Args:
        data: Datos a retornar
        message: Mensaje opcional
    
    Returns:
        Flask response object
    """
    return format_response(data, message, 'success')

def create_error_response(message, status_code=400, error_code=None):
    """
    Crea respuesta de error estándar
    
    Args:
        message: Mensaje de error
        status_code: Código de estado HTTP
        error_code: Código de error personalizado
    
    Returns:
        Flask response object
    """
    response = {
        'status': 'error',
        'timestamp': datetime.now().isoformat(),
        'error': {
            'message': message
        }
    }
    
    if error_code:
        response['error']['code'] = error_code
    
    return jsonify(response), status_code