# Agregar estas importaciones al inicio del archivo
from datetime import datetime, timedelta
import pytz

@registros_bp.route('/registros_hoy', methods=['GET'])
def get_registros_hoy():
    """Obtiene los registros de hoy"""
    try:
        # Obtener la fecha de "hoy" considerando la zona horaria
        # Asumiendo que estás en Chile (Santiago)
        tz_santiago = pytz.timezone('America/Santiago')
        fecha_hoy_local = datetime.now(tz_santiago).date()
        
        # Query principal usando la fecha calculada en Python
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
        WHERE DATE(er.fecha) = %s
        ORDER BY er.hora DESC
        """
        
        registros = execute_query(query, (fecha_hoy_local,))
        
        return format_response(format_registros(registros))
        
    except Exception as e:
        return handle_error(e, "Error al obtener registros de hoy")

# Versión alternativa sin pytz (si no está instalado)
@registros_bp.route('/registros_hoy_v2', methods=['GET'])
def get_registros_hoy_v2():
    """Obtiene los registros de hoy (versión alternativa)"""
    try:
        # Obtener fecha actual del sistema
        fecha_hoy = datetime.now().date()
        
        # Query usando parámetro en lugar de CURDATE()
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
        WHERE DATE(er.fecha) = %s
        ORDER BY er.hora DESC
        """
        
        registros = execute_query(query, (fecha_hoy,))
        
        # Incluir información adicional en la respuesta
        response_data = {
            'fecha_consultada': fecha_hoy.strftime('%Y-%m-%d'),
            'total_registros': len(registros),
            'registros': format_registros(registros)
        }
        
        return format_response(response_data)
        
    except Exception as e:
        return handle_error(e, "Error al obtener registros de hoy")

# Endpoint de diagnóstico para verificar fechas
@registros_bp.route('/registros/diagnostico', methods=['GET'])
def diagnostico_fechas():
    """Endpoint de diagnóstico para verificar problemas con fechas"""
    try:
        # Información del servidor
        query_servidor = """
        SELECT 
            CURDATE() as fecha_servidor,
            NOW() as fecha_hora_servidor,
            @@system_time_zone as zona_horaria_sistema,
            @@time_zone as zona_horaria_sesion
        """
        info_servidor = execute_query(query_servidor, fetch_one=True)
        
        # Últimos registros con sus fechas
        query_ultimos = """
        SELECT 
            fecha,
            MIN(hora) as primera_hora,
            MAX(hora) as ultima_hora,
            COUNT(*) as total_registros
        FROM EST_registros
        GROUP BY fecha
        ORDER BY fecha DESC
        LIMIT 5
        """
        ultimos_dias = execute_query(query_ultimos)
        
        # Fecha actual en Python
        fecha_python = datetime.now()
        
        # Si tienes pytz instalado
        try:
            import pytz
            tz_santiago = pytz.timezone('America/Santiago')
            fecha_santiago = datetime.now(tz_santiago)
            fecha_info_santiago = {
                'fecha': fecha_santiago.strftime('%Y-%m-%d'),
                'hora': fecha_santiago.strftime('%H:%M:%S'),
                'timezone': 'America/Santiago'
            }
        except ImportError:
            fecha_info_santiago = {'error': 'pytz no instalado'}
        
        diagnostico = {
            'servidor_mysql': {
                'fecha': info_servidor['fecha_servidor'].strftime('%Y-%m-%d') if info_servidor else 'N/A',
                'fecha_hora': info_servidor['fecha_hora_servidor'].strftime('%Y-%m-%d %H:%M:%S') if info_servidor else 'N/A',
                'zona_horaria_sistema': info_servidor['zona_horaria_sistema'] if info_servidor else 'N/A',
                'zona_horaria_sesion': info_servidor['zona_horaria_sesion'] if info_servidor else 'N/A'
            },
            'servidor_python': {
                'fecha': fecha_python.strftime('%Y-%m-%d'),
                'hora': fecha_python.strftime('%H:%M:%S')
            },
            'fecha_santiago': fecha_info_santiago,
            'ultimos_dias_con_registros': [
                {
                    'fecha': dia['fecha'].strftime('%Y-%m-%d'),
                    'primera_hora': str(dia['primera_hora']),
                    'ultima_hora': str(dia['ultima_hora']),
                    'total_registros': dia['total_registros']
                } for dia in ultimos_dias
            ]
        }
        
        return format_response(diagnostico)
        
    except Exception as e:
        return handle_error(e, "Error en diagnóstico")
