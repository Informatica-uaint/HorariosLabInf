# routes/registros_estudiantes.py - Rutas para manejo de registros de estudiantes (Migrado a API unificada)
from flask import Blueprint, request, jsonify
from database import get_connection
from utils.helpers import format_response, handle_error
from datetime import datetime, timedelta
import logging

registros_estudiantes_bp = Blueprint('registros_estudiantes', __name__)

def execute_query_registros(query, params=None, fetch_one=False):
    """Ejecuta consulta con conexión PyMySQL para registros de estudiantes"""
    connection = get_connection()
    try:
        # Usar DictCursor para obtener diccionarios en lugar de tuplas
        import pymysql
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute(query, params or ())

        if query.strip().upper().startswith('SELECT'):
            if fetch_one:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
        else:
            connection.commit()
            result = {
                'affected_rows': cursor.rowcount,
                'last_insert_id': cursor.lastrowid
            }

        return result
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        connection.close()

@registros_estudiantes_bp.route('/registros_estudiantes', methods=['GET'])
def get_registros():
    """Obtiene todos los registros de estudiantes"""
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

        registros = execute_query_registros(query)
        return format_response(format_registros(registros))

    except Exception as e:
        return handle_error(e, "Error al obtener registros")

@registros_estudiantes_bp.route('/registros_hoy', methods=['GET'])
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

        registros = execute_query_registros(query)
        return format_response(format_registros(registros))

    except Exception as e:
        return handle_error(e, "Error al obtener registros de hoy")

@registros_estudiantes_bp.route('/registros_semana', methods=['GET'])
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

        registros = execute_query_registros(query)
        return format_response(format_registros(registros))

    except Exception as e:
        return handle_error(e, "Error al obtener registros de la semana")

@registros_estudiantes_bp.route('/registros_mes', methods=['GET'])
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

        registros = execute_query_registros(query)
        return format_response(format_registros(registros))

    except Exception as e:
        return handle_error(e, "Error al obtener registros del mes")

@registros_estudiantes_bp.route('/registros_entre_fechas', methods=['GET'])
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

        registros = execute_query_registros(query, (inicio, fin))
        return format_response(format_registros(registros))

    except Exception as e:
        return handle_error(e, "Error al obtener registros entre fechas")

@registros_estudiantes_bp.route('/registros_estudiantes', methods=['POST'])
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

        result = execute_query_registros(query, (
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

@registros_estudiantes_bp.route('/registros_estudiantes/<registro_id>', methods=['GET'])
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

        registro = execute_query_registros(query, (registro_id,), fetch_one=True)

        if not registro:
            return jsonify({'error': 'Registro no encontrado'}), 404

        formatted_registro = format_registros([registro])[0]
        return format_response(formatted_registro)

    except Exception as e:
        return handle_error(e, "Error al obtener registro")

@registros_estudiantes_bp.route('/registros_estudiantes/<registro_id>', methods=['DELETE'])
def delete_registro(registro_id):
    """Elimina un registro"""
    try:
        # Verificar que el registro existe
        query_exists = "SELECT id FROM EST_registros WHERE id = %s"
        existing = execute_query_registros(query_exists, (registro_id,), fetch_one=True)

        if not existing:
            return jsonify({'error': 'Registro no encontrado'}), 404

        # Eliminar registro
        query_delete = "DELETE FROM EST_registros WHERE id = %s"
        execute_query_registros(query_delete, (registro_id,))

        return format_response({'mensaje': 'Registro eliminado exitosamente'})

    except Exception as e:
        return handle_error(e, "Error al eliminar registro")

@registros_estudiantes_bp.route('/registros/estudiante/<estudiante_id>', methods=['GET'])
def get_registros_estudiante(estudiante_id):
    """Obtiene todos los registros de un estudiante específico"""
    try:
        # Obtener email del estudiante
        query_estudiante = "SELECT email FROM usuarios_estudiantes WHERE id = %s"
        estudiante = execute_query_registros(query_estudiante, (estudiante_id,), fetch_one=True)

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

        registros = execute_query_registros(query, (estudiante_id, estudiante[0]))  # estudiante[0] es el email
        return format_response(format_registros(registros))

    except Exception as e:
        return handle_error(e, "Error al obtener registros del estudiante")

def format_registros(registros):
    """Formatea la lista de registros para la respuesta"""
    formatted = []

    for reg in registros:
        try:
            # Acceder por clave para diccionarios de PyMySQL DictCursor
            reg_id = reg['id']
            fecha = reg['fecha']
            hora_registro = reg['horaRegistro']
            nombre_estudiante = reg['nombreEstudiante']
            apellido_estudiante = reg['apellidoEstudiante']
            rut_estudiante = reg['rutEstudiante']
            email = reg['email']
            tipo_registro = reg['tipoRegistro']
            estudiante_id = reg['estudianteId']

            # Manejar fecha
            if isinstance(fecha, str):
                fecha_str = fecha
            else:
                fecha_str = fecha.strftime('%Y-%m-%d') if hasattr(fecha, 'strftime') else str(fecha)

            # Manejar hora - SOLUCIÓN PARA TIMEDELTA
            if isinstance(hora_registro, str):
                # Si ya es string, usarlo directamente
                hora_str = hora_registro
            elif isinstance(hora_registro, timedelta):
                # Convertir timedelta a string de hora
                total_seconds = int(hora_registro.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                hora_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            elif hasattr(hora_registro, 'strftime'):
                # Si es un objeto time o datetime
                hora_str = hora_registro.strftime('%H:%M:%S')
            else:
                # Default para casos inesperados
                logging.warning(f"Tipo de hora inesperado: {type(hora_registro)} - {hora_registro}")
                hora_str = "00:00:00"

            # Crear timestamp combinando fecha y hora
            timestamp_str = f"{fecha_str} {hora_str}"

            # Convertir a datetime para generar ISO format
            try:
                fecha_hora = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                iso_timestamp = fecha_hora.isoformat()
            except ValueError as e:
                logging.error(f"Error al parsear timestamp: {timestamp_str} - {e}")
                # Si falla el parsing, usar la fecha actual como fallback
                iso_timestamp = datetime.now().isoformat()

            formatted.append({
                'id': str(reg_id),
                'estudianteId': str(estudiante_id) if estudiante_id else '',
                'nombreEstudiante': nombre_estudiante or '',
                'apellidoEstudiante': apellido_estudiante or '',
                'rutEstudiante': rut_estudiante or '',
                'tipoRegistro': tipo_registro or '',
                'horaRegistro': iso_timestamp,
                'fecha': fecha_str
            })

        except Exception as e:
            # Log detallado del error
            logging.error(f"Error formatting registro {reg.get('id', 'unknown')}: {e}")
            logging.error(f"Registro completo: {reg}")

            # Crear entrada con datos básicos si falla el formateo
            now = datetime.now()
            formatted.append({
                'id': str(reg[0] if len(reg) > 0 else ''),
                'estudianteId': str(reg[8] if len(reg) > 8 else ''),
                'nombreEstudiante': reg[3] if len(reg) > 3 else '',
                'apellidoEstudiante': reg[4] if len(reg) > 4 else '',
                'rutEstudiante': reg[5] if len(reg) > 5 else '',
                'tipoRegistro': reg[7] if len(reg) > 7 else '',
                'horaRegistro': now.isoformat(),
                'fecha': now.date().isoformat()
            })

    return formatted