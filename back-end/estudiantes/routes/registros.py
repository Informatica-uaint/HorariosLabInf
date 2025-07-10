# routes/registros.py - Rutas para manejo de registros
from flask import Blueprint, request, jsonify
from config.database import execute_query
from utils.helpers import format_response, handle_error
from datetime import datetime, timedelta
import logging

registros_bp = Blueprint('registros', __name__)

@registros_bp.route('/registros', methods=['GET'])
def get_registros():
    """Obtiene todos los registros"""
    try:
        query = """
        SELECT 
            er.id,
            er.fecha,
            er.hora as horaRegistro,
            er.nombre as nombreEstudiante,
            er.apellido as apellidoEstudiante,
            '' as rutEstudiante,
            er.email,
            LOWER(er.tipo) as tipoRegistro,
            ue.id as estudianteId
        FROM EST_registros er
        LEFT JOIN usuarios_estudiantes ue ON er.email = ue.email
        ORDER BY er.fecha DESC, er.hora DESC
        """
        
        registros = execute_query(query)
        return format_response(format_registros(registros))
        
    except Exception as e:
        return handle_error(e, "Error al obtener registros")

@registros_bp.route('/registros_hoy', methods=['GET'])
def get_registros_hoy():
    """Obtiene los registros de hoy"""
    try:
        query = """
        SELECT 
            er.id,
            er.fecha,
            er.hora as horaRegistro,
            er.nombre as nombreEstudiante,
            er.apellido as apellidoEstudiante,
            '' as rutEstudiante,
            er.email,
            LOWER(er.tipo) as tipoRegistro,
            ue.id as estudianteId
        FROM EST_registros er
        LEFT JOIN usuarios_estudiantes ue ON er.email = ue.email
        WHERE DATE(er.fecha) = CURDATE()
        ORDER BY er.hora DESC
        """
        
        registros = execute_query(query)
        return format_response(format_registros(registros))
        
    except Exception as e:
        return handle_error(e, "Error al obtener registros de hoy")

@registros_bp.route('/registros_semana', methods=['GET'])
def get_registros_semana():
    """Obtiene los registros de esta semana"""
    try:
        query = """
        SELECT 
            er.id,
            er.fecha,
            er.hora as horaRegistro,
            er.nombre as nombreEstudiante,
            er.apellido as apellidoEstudiante,
            '' as rutEstudiante,
            er.email,
            LOWER(er.tipo) as tipoRegistro,
            ue.id as estudianteId
        FROM EST_registros er
        LEFT JOIN usuarios_estudiantes ue ON er.email = ue.email
        WHERE YEARWEEK(er.fecha, 1) = YEARWEEK(CURDATE(), 1)
        ORDER BY er.fecha DESC, er.hora DESC
        """
        
        registros = execute_query(query)
        return format_response(format_registros(registros))
        
    except Exception as e:
        return handle_error(e, "Error al obtener registros de la semana")

@registros_bp.route('/registros_mes', methods=['GET'])
def get_registros_mes():
    """Obtiene los registros de este mes"""
    try:
        query = """
        SELECT 
            er.id,
            er.fecha,
            er.hora as horaRegistro,
            er.nombre as nombreEstudiante,
            er.apellido as apellidoEstudiante,
            '' as rutEstudiante,
            er.email,
            LOWER(er.tipo) as tipoRegistro,
            ue.id as estudianteId
        FROM EST_registros er
        LEFT JOIN usuarios_estudiantes ue ON er.email = ue.email
        WHERE YEAR(er.fecha) = YEAR(CURDATE()) AND MONTH(er.fecha) = MONTH(CURDATE())
        ORDER BY er.fecha DESC, er.hora DESC
        """
        
        registros = execute_query(query)
        return format_response(format_registros(registros))
        
    except Exception as e:
        return handle_error(e, "Error al obtener registros del mes")

@registros_bp.route('/registros_entre_fechas', methods=['GET'])
def get_registros_entre_fechas():
    """Obtiene registros entre dos fechas"""
    try:
        inicio = request.args.get('inicio')
        fin = request.args.get('fin')
        
        if not inicio or not fin:
            return jsonify({'error': 'Se requieren las fechas de inicio y fin'}), 400
        
        try:
            # Validar formato de fechas
            datetime.strptime(inicio, '%Y-%m-%d')
            datetime.strptime(fin, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
        
        query = """
        SELECT 
            er.id,
            er.fecha,
            er.hora as horaRegistro,
            er.nombre as nombreEstudiante,
            er.apellido as apellidoEstudiante,
            '' as rutEstudiante,
            er.email,
            LOWER(er.tipo) as tipoRegistro,
            ue.id as estudianteId
        FROM EST_registros er
        LEFT JOIN usuarios_estudiantes ue ON er.email = ue.email
        WHERE er.fecha BETWEEN %s AND %s
        ORDER BY er.fecha DESC, er.hora DESC
        """
        
        registros = execute_query(query, (inicio, fin))
        return format_response(format_registros(registros))
        
    except Exception as e:
        return handle_error(e, "Error al obtener registros entre fechas")

@registros_bp.route('/registros', methods=['POST'])
def create_registro():
    """Crea un nuevo registro manual"""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['nombre', 'apellido', 'email', 'tipo']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'error': f'Faltan campos requeridos: {", ".join(missing_fields)}'
            }), 400
        
        # Validar tipo de registro
        if data['tipo'].lower() not in ['entrada', 'salida']:
            return jsonify({'error': 'Tipo de registro debe ser "entrada" o "salida"'}), 400
        
        # Obtener fecha y hora actual o usar las proporcionadas
        fecha = data.get('fecha', datetime.now().date())
        hora = data.get('hora', datetime.now().time())
        
        if isinstance(fecha, str):
            fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
        if isinstance(hora, str):
            hora = datetime.strptime(hora, '%H:%M:%S').time()
        
        # Insertar registro
        query = """
        INSERT INTO EST_registros (fecha, hora, dia, nombre, apellido, email, tipo, auto_generado)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        result = execute_query(query, (
            fecha,
            hora,
            fecha.strftime('%A'),  # Día de la semana
            data['nombre'].strip(),
            data['apellido'].strip(),
            data['email'].strip().lower(),
            data['tipo'].capitalize(),
            data.get('auto_generado', False)
        ))
        
        return format_response({
            'id': result['last_insert_id'],
            'mensaje': 'Registro creado exitosamente'
        }), 201
        
    except Exception as e:
        return handle_error(e, "Error al crear registro")

@registros_bp.route('/registros/<registro_id>', methods=['GET'])
def get_registro(registro_id):
    """Obtiene un registro específico"""
    try:
        query = """
        SELECT 
            er.id,
            er.fecha,
            er.hora as horaRegistro,
            er.nombre as nombreEstudiante,
            er.apellido as apellidoEstudiante,
            '' as rutEstudiante,
            er.email,
            LOWER(er.tipo) as tipoRegistro,
            ue.id as estudianteId,
            er.auto_generado
        FROM EST_registros er
        LEFT JOIN usuarios_estudiantes ue ON er.email = ue.email
        WHERE er.id = %s
        """
        
        registro = execute_query(query, (registro_id,), fetch_one=True)
        
        if not registro:
            return jsonify({'error': 'Registro no encontrado'}), 404
        
        formatted_registro = format_registros([registro])[0]
        return format_response(formatted_registro)
        
    except Exception as e:
        return handle_error(e, "Error al obtener registro")

@registros_bp.route('/registros/<registro_id>', methods=['DELETE'])
def delete_registro(registro_id):
    """Elimina un registro"""
    try:
        # Verificar que el registro existe
        query_exists = "SELECT id FROM EST_registros WHERE id = %s"
        existing = execute_query(query_exists, (registro_id,), fetch_one=True)
        
        if not existing:
            return jsonify({'error': 'Registro no encontrado'}), 404
        
        # Eliminar registro
        query_delete = "DELETE FROM EST_registros WHERE id = %s"
        execute_query(query_delete, (registro_id,))
        
        return format_response({'mensaje': 'Registro eliminado exitosamente'})
        
    except Exception as e:
        return handle_error(e, "Error al eliminar registro")

@registros_bp.route('/registros/estudiante/<estudiante_id>', methods=['GET'])
def get_registros_estudiante(estudiante_id):
    """Obtiene todos los registros de un estudiante específico"""
    try:
        # Obtener email del estudiante
        query_estudiante = "SELECT email FROM usuarios_estudiantes WHERE id = %s"
        estudiante = execute_query(query_estudiante, (estudiante_id,), fetch_one=True)
        
        if not estudiante:
            return jsonify({'error': 'Estudiante no encontrado'}), 404
        
        # Obtener registros del estudiante
        query = """
        SELECT 
            er.id,
            er.fecha,
            er.hora as horaRegistro,
            er.nombre as nombreEstudiante,
            er.apellido as apellidoEstudiante,
            '' as rutEstudiante,
            er.email,
            LOWER(er.tipo) as tipoRegistro,
            %s as estudianteId
        FROM EST_registros er
        WHERE er.email = %s
        ORDER BY er.fecha DESC, er.hora DESC
        """
        
        registros = execute_query(query, (estudiante_id, estudiante['email']))
        return format_response(format_registros(registros))
        
    except Exception as e:
        return handle_error(e, "Error al obtener registros del estudiante")

def format_registros(registros):
    """Formatea la lista de registros para la respuesta"""
    formatted = []
    
    for reg in registros:
        try:
            # Manejar fecha
            if isinstance(reg['fecha'], str):
                fecha_obj = datetime.strptime(reg['fecha'], '%Y-%m-%d').date()
            else:
                fecha_obj = reg['fecha']
            
            # Manejar hora - FIXED: manejo correcto de timedelta
            hora_registro = reg['horaRegistro']
            
            if isinstance(hora_registro, str):
                # Si es string, parsear como tiempo
                try:
                    hora_obj = datetime.strptime(hora_registro, '%H:%M:%S').time()
                except ValueError:
                    try:
                        hora_obj = datetime.strptime(hora_registro, '%H:%M').time()
                    except ValueError:
                        hora_obj = datetime.now().time()
            elif isinstance(hora_registro, timedelta):
                # Si es timedelta (duración desde medianoche) - ESTA ES LA CORRECCIÓN
                total_seconds = int(hora_registro.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                hora_obj = datetime.time(hours, minutes, seconds)
            elif hasattr(hora_registro, 'hour'):
                # Si ya es time object
                hora_obj = hora_registro
            else:
                # Default a hora actual si no se puede procesar
                hora_obj = datetime.now().time()
            
            # Combinar fecha y hora
            fecha_hora = datetime.combine(fecha_obj, hora_obj)
            
            formatted.append({
                'id': str(reg['id']),
                'estudianteId': str(reg['estudianteId']) if reg['estudianteId'] else '',
                'nombreEstudiante': reg['nombreEstudiante'],
                'apellidoEstudiante': reg['apellidoEstudiante'],
                'rutEstudiante': reg['rutEstudiante'],
                'tipoRegistro': reg['tipoRegistro'],
                'horaRegistro': fecha_hora.isoformat(),
                'fecha': fecha_obj.isoformat()
            })
            
        except Exception as e:
            # Log del error y continuar con el siguiente registro
            logging.error(f"Error formatting registro {reg.get('id', 'unknown')}: {e}")
            
            # Crear entrada con datos básicos si falla el formateo
            formatted.append({
                'id': str(reg.get('id', '')),
                'estudianteId': str(reg.get('estudianteId', '')),
                'nombreEstudiante': reg.get('nombreEstudiante', ''),
                'apellidoEstudiante': reg.get('apellidoEstudiante', ''),
                'rutEstudiante': reg.get('rutEstudiante', ''),
                'tipoRegistro': reg.get('tipoRegistro', ''),
                'horaRegistro': datetime.now().isoformat(),
                'fecha': datetime.now().date().isoformat()
            })
    
    return formatted
