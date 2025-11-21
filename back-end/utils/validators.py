# utils/validators.py - Funciones de validación
import re
from datetime import datetime

def validate_email(email):
    """Valida formato de email"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_required_fields(data, required_fields):
    """Valida que todos los campos requeridos estén presentes"""
    if not data:
        return False
    
    for field in required_fields:
        if field not in data or not data[field] or str(data[field]).strip() == '':
            return False
    
    return True

def validate_qr_data(qr_data):
    """Valida la estructura de datos del código QR"""
    if not isinstance(qr_data, dict):
        return {
            'valid': False,
            'message': 'Datos QR deben ser un objeto JSON válido'
        }
    
    # Campos requeridos para QR de estudiante
    required_fields = ['name', 'surname', 'email', 'tipoUsuario']
    
    for field in required_fields:
        if field not in qr_data:
            return {
                'valid': False,
                'message': f'Campo requerido faltante: {field}'
            }
    
    # Validar tipo de usuario
    if qr_data.get('tipoUsuario') != 'ESTUDIANTE':
        return {
            'valid': False,
            'message': 'Tipo de usuario inválido'
        }
    
    # Validar email
    if not validate_email(qr_data['email']):
        return {
            'valid': False,
            'message': 'Email inválido en código QR'
        }
    
    # Validar que nombre y apellido no estén vacíos
    if not qr_data['name'].strip() or not qr_data['surname'].strip():
        return {
            'valid': False,
            'message': 'Nombre y apellido son requeridos'
        }
    
    # Validar timestamp si está presente
    if 'timestamp' in qr_data:
        try:
            timestamp = int(qr_data['timestamp'])
            # Verificar que el timestamp no sea muy antiguo (más de 1 hora)
            current_time = datetime.now().timestamp() * 1000
            if current_time - timestamp > 3600000:  # 1 hora en milisegundos
                return {
                    'valid': False,
                    'message': 'Código QR demasiado antiguo'
                }
        except (ValueError, TypeError):
            return {
                'valid': False,
                'message': 'Timestamp inválido en código QR'
            }
    
    # Validar estado si está presente
    if 'status' in qr_data and qr_data['status'] == 'EXPIRED':
        return {
            'valid': False,
            'message': 'Código QR marcado como expirado'
        }
    
    return {
        'valid': True,
        'message': 'Código QR válido'
    }

def validate_date_format(date_string, format_string='%Y-%m-%d'):
    """Valida formato de fecha"""
    try:
        datetime.strptime(date_string, format_string)
        return True
    except ValueError:
        return False

def validate_time_format(time_string, format_string='%H:%M:%S'):
    """Valida formato de hora"""
    try:
        datetime.strptime(time_string, format_string)
        return True
    except ValueError:
        return False

def validate_registro_type(tipo):
    """Valida tipo de registro"""
    return tipo.lower() in ['entrada', 'salida']

def sanitize_string(text, max_length=None):
    """Limpia y sanitiza strings"""
    if not text:
        return ''
    
    # Remover espacios al inicio y final
    cleaned = str(text).strip()
    
    # Remover caracteres especiales peligrosos
    cleaned = re.sub(r'[<>"\']', '', cleaned)
    
    # Limitar longitud si se especifica
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned

def validate_student_data(data):
    """Valida datos completos de estudiante"""
    errors = []
    
    # Validar campos requeridos
    required_fields = ['nombre', 'apellido', 'email']
    for field in required_fields:
        if not data.get(field) or not str(data[field]).strip():
            errors.append(f'{field} es requerido')
    
    # Validar email
    if data.get('email') and not validate_email(data['email']):
        errors.append('Email tiene formato inválido')
    
    # Validar longitud de campos
    if data.get('nombre') and len(data['nombre']) > 100:
        errors.append('Nombre demasiado largo (máximo 100 caracteres)')
    
    if data.get('apellido') and len(data['apellido']) > 100:
        errors.append('Apellido demasiado largo (máximo 100 caracteres)')
    
    if data.get('email') and len(data['email']) > 100:
        errors.append('Email demasiado largo (máximo 100 caracteres)')
    
    if data.get('carrera') and len(data['carrera']) > 50:
        errors.append('Carrera demasiado larga (máximo 50 caracteres)')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }