# routes/qr.py - Rutas para manejo de códigos QR y autenticación
from flask import Blueprint, request, jsonify
from config.database import execute_query
from utils.helpers import format_response, handle_error
from utils.validators import validate_email, validate_qr_data
from datetime import datetime, timedelta
import json
import logging

qr_bp = Blueprint('qr', __name__)

@qr_bp.route('/qr/validate', methods=['POST'])
def validate_qr():
    """Valida un código QR y registra entrada/salida"""
    try:
        data = request.get_json()
        
        if not data or 'qr_data' not in data:
            return jsonify({'error': 'Datos QR requeridos'}), 400
        
        # Intentar parsear los datos del QR
        try:
            qr_info = json.loads(data['qr_data'])
        except json.JSONDecodeError:
            return jsonify({'error': 'Formato de QR inválido'}), 400
        
        # Validar estructura del QR
        validation_result = validate_qr_data(qr_info)
        if not validation_result['valid']:
            return jsonify({'error': validation_result['message']}), 400
        
        # Verificar si el QR está expirado (solo si no tiene auto-renovación)
        if not qr_info.get('autoRenewal', False):
            timestamp = qr_info.get('timestamp', 0)
            current_time = datetime.now().timestamp() * 1000  # Convertir a milisegundos
            
            # QR expira después de 15 segundos
            if current_time - timestamp > 15000:
                return jsonify({
                    'error': 'Código QR expirado',
                    'expired': True
                }), 400
        
        # Buscar o crear el estudiante
        email = qr_info['email'].strip().lower()
        estudiante = get_or_create_estudiante(qr_info)
        
        if not estudiante:
            return jsonify({'error': 'Error al procesar datos del estudiante'}), 500
        
        # Determinar tipo de registro (entrada/salida)
        tipo_registro = determine_registro_type(email)
        
        # Registrar entrada/salida
        registro_id = create_registro_from_qr(estudiante, tipo_registro, qr_info)
        
        return format_response({
            'success': True,
            'estudiante': {
                'id': estudiante['id'],
                'nombre': estudiante['nombre'],
                'apellido': estudiante['apellido'],
                'email': estudiante['email']
            },
            'registro': {
                'id': registro_id,
                'tipo': tipo_registro,
                'timestamp': datetime.now().isoformat()
            },
            'mensaje': f'{tipo_registro.capitalize()} registrada exitosamente'
        })
        
    except Exception as e:
        return handle_error(e, "Error al validar código QR")

@qr_bp.route('/qr/generate', methods=['POST'])
def generate_qr_data():
    """Genera datos para un código QR (usado internamente)"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'surname', 'email']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'error': f'Faltan campos requeridos: {", ".join(missing_fields)}'
            }), 400
        
        if not validate_email(data['email']):
            return jsonify({'error': 'Email inválido'}), 400
        
        # Generar datos del QR
        qr_data = {
            'name': data['name'].strip(),
            'surname': data['surname'].strip(),
            'email': data['email'].strip().lower(),
            'timestamp': int(datetime.now().timestamp() * 1000),
            'tipoUsuario': 'ESTUDIANTE',
            'status': 'VALID'
        }
        
        # Agregar auto-renovación si se especifica
        if data.get('autoRenewal', False):
            qr_data['autoRenewal'] = True
        
        return format_response({
            'qr_data': json.dumps(qr_data),
            'expires_at': datetime.now() + timedelta(seconds=15) if not data.get('autoRenewal') else None
        })
        
    except Exception as e:
        return handle_error(e, "Error al generar datos QR")

@qr_bp.route('/qr/status/<email>', methods=['GET'])
def get_qr_status(email):
    """Obtiene el estado actual de un estudiante para QR"""
    try:
        if not validate_email(email):
            return jsonify({'error': 'Email inválido'}), 400
        
        # Buscar estudiante
        query_estudiante = "SELECT * FROM usuarios_estudiantes WHERE email = %s"
        estudiante = execute_query(query_estudiante, (email.lower(),), fetch_one=True)
        
        if not estudiante:
            return jsonify({'error': 'Estudiante no encontrado'}), 404
        
        # Obtener último registro del día
        query_ultimo = """
        SELECT tipo, hora, fecha 
        FROM EST_registros 
        WHERE email = %s AND DATE(fecha) = CURDATE()
        ORDER BY fecha DESC, hora DESC 
        LIMIT 1
        """
        
        ultimo_registro = execute_query(query_ultimo, (email.lower(),), fetch_one=True)
        
        # Determinar estado actual
        if ultimo_registro:
            presente = ultimo_registro['tipo'] == 'Entrada'
            ultimo_movimiento = {
                'tipo': ultimo_registro['tipo'],
                'hora': str(ultimo_registro['hora']),
                'fecha': ultimo_registro['fecha'].strftime('%Y-%m-%d')
            }
        else:
            presente = False
            ultimo_movimiento = None
        
        return format_response({
            'estudiante': {
                'id': estudiante['id'],
                'nombre': estudiante['nombre'],
                'apellido': estudiante['apellido'],
                'email': estudiante['email'],
                'activo': bool(estudiante['activo'])
            },
            'presente': presente,
            'ultimo_movimiento': ultimo_movimiento,
            'proximo_tipo': 'Salida' if presente else 'Entrada'
        })
        
    except Exception as e:
        return handle_error(e, "Error al obtener estado QR")

def get_or_create_estudiante(qr_info):
    """Busca un estudiante o lo crea si no existe"""
    try:
        email = qr_info['email'].strip().lower()
        
        # Buscar estudiante existente
        query_search = "SELECT * FROM usuarios_estudiantes WHERE email = %s"
        estudiante = execute_query(query_search, (email,), fetch_one=True)
        
        if estudiante:
            return estudiante
        
        # Crear nuevo estudiante
        query_insert = """
        INSERT INTO usuarios_estudiantes (nombre, apellido, email, activo, TP)
        VALUES (%s, %s, %s, 1, 'No especificado')
        """
        
        result = execute_query(query_insert, (
            qr_info['name'].strip(),
            qr_info['surname'].strip(),
            email
        ))
        
        # Retornar el estudiante recién creado
        return {
            'id': result['last_insert_id'],
            'nombre': qr_info['name'].strip(),
            'apellido': qr_info['surname'].strip(),
            'email': email,
            'activo': True,
            'TP': 'No especificado'
        }
        
    except Exception as e:
        logging.error(f"Error al obtener/crear estudiante: {e}")
        return None

def determine_registro_type(email):
    """Determina si el próximo registro debe ser entrada o salida"""
    try:
        # Obtener el último registro del día
        query = """
        SELECT tipo 
        FROM EST_registros 
        WHERE email = %s AND DATE(fecha) = CURDATE()
        ORDER BY fecha DESC, hora DESC 
        LIMIT 1
        """
        
        ultimo_registro = execute_query(query, (email,), fetch_one=True)
        
        if not ultimo_registro:
            return 'Entrada'  # Primera vez del día
        
        # Alternar entre entrada y salida
        return 'Salida' if ultimo_registro['tipo'] == 'Entrada' else 'Entrada'
        
    except Exception as e:
        logging.error(f"Error al determinar tipo de registro: {e}")
        return 'Entrada'  # Default a entrada en caso de error

def create_registro_from_qr(estudiante, tipo_registro, qr_info):
    """Crea un registro basado en datos del QR"""
    try:
        now = datetime.now()
        
        query = """
        INSERT INTO EST_registros (fecha, hora, dia, nombre, apellido, email, tipo, auto_generado)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
        """
        
        result = execute_query(query, (
            now.date(),
            now.time(),
            now.strftime('%A'),
            estudiante['nombre'],
            estudiante['apellido'],
            estudiante['email'],
            tipo_registro
        ))
        
        return result['last_insert_id']
        
    except Exception as e:
        logging.error(f"Error al crear registro desde QR: {e}")
        raise

@qr_bp.route('/qr/history/<email>', methods=['GET'])
def get_qr_history(email):
    """Obtiene el historial de registros QR para un email"""
    try:
        if not validate_email(email):
            return jsonify({'error': 'Email inválido'}), 400
        
        # Obtener parámetros de consulta
        limit = request.args.get('limit', 50, type=int)
        days = request.args.get('days', 30, type=int)
        
        # Validar límites
        limit = min(limit, 100)  # Máximo 100 registros
        days = min(days, 365)    # Máximo 1 año
        
        query = """
        SELECT 
            id, fecha, hora, tipo,
            CONCAT(fecha, ' ', hora) as timestamp_completo
        FROM EST_registros 
        WHERE email = %s 
        AND fecha >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        ORDER BY fecha DESC, hora DESC 
        LIMIT %s
        """
        
        registros = execute_query(query, (email.lower(), days, limit))
        
        # Formatear respuesta
        formatted_registros = []
        for reg in registros:
            formatted_registros.append({
                'id': reg['id'],
                'fecha': reg['fecha'].strftime('%Y-%m-%d'),
                'hora': str(reg['hora']),
                'tipo': reg['tipo'],
                'timestamp': reg['timestamp_completo'].strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return format_response({
            'email': email,
            'registros': formatted_registros,
            'total': len(formatted_registros)
        })
        
    except Exception as e:
        return handle_error(e, "Error al obtener historial QR")