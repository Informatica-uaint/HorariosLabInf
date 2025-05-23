from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from database import get_connection
from utils.datetime_utils import get_current_datetime
from config import Config

registros_bp = Blueprint('registros', __name__)

@registros_bp.route('/registros', methods=['GET'])
def get_registros():
    """Obtener todos los registros"""
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM registros ORDER BY fecha DESC, hora DESC")
            registros = cursor.fetchall()
            
            # Convertir valores problemáticos
            for reg in registros:
                for key, value in reg.items():
                    if isinstance(value, datetime):
                        reg[key] = value.isoformat()
                    elif isinstance(value, timedelta):
                        reg[key] = str(value)
        
        conn.close()
        return jsonify(registros)
    except Exception as e:
        print(f"Error en get_registros: {str(e)}")
        return jsonify({"error": str(e)}), 500

@registros_bp.route('/registros_hoy', methods=['GET'])
def get_registros_hoy():
    """Obtener registros del día actual"""
    try:
        conn = get_connection()
        today = get_current_datetime().strftime('%Y-%m-%d')
        
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, fecha, hora, dia, nombre, apellido, email, tipo
                FROM registros 
                WHERE fecha = %s 
                ORDER BY hora DESC
            """, (today,))
            registros = cursor.fetchall()
            
            # Convertir a formato serializable
            serializable_registros = []
            for reg in registros:
                serializable_reg = {}
                for key, value in reg.items():
                    if isinstance(value, datetime):
                        serializable_reg[key] = value.isoformat()
                    elif isinstance(value, timedelta):
                        serializable_reg[key] = str(value)
                    elif hasattr(value, 'isoformat') and callable(value.isoformat):
                        serializable_reg[key] = value.isoformat()
                    else:
                        serializable_reg[key] = value
                serializable_registros.append(serializable_reg)
            
        conn.close()
        return jsonify(serializable_registros if serializable_registros else [])
    except Exception as e:
        print(f"Error al obtener registros de hoy: {str(e)}")
        return jsonify({"error": str(e)}), 500

@registros_bp.route('/registros', methods=['POST'])
def add_registro():
    """Agregar nuevo registro de entrada/salida"""
    data = request.get_json()
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # Obtener fecha y hora actuales
            now = get_current_datetime()
            fecha = data.get('fecha', now.strftime("%Y-%m-%d"))
            hora = data.get('hora', now.strftime("%H:%M:%S"))
            timestamp_value = data.get('timestamp', None)

            if timestamp_value:
                if isinstance(timestamp_value, int) and timestamp_value > 1e11:
                    timestamp = datetime.fromtimestamp(timestamp_value / 1000)
                elif isinstance(timestamp_value, str) and timestamp_value.isdigit() and len(timestamp_value) > 11:
                    timestamp = datetime.fromtimestamp(int(timestamp_value) / 1000)
                else:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_value)
                    except Exception:
                        timestamp = now
            else:
                timestamp = now
            
            # Obtener día de la semana en español
            if 'dia' in data and data['dia']:
                dia = data['dia']
            else:
                day_name = now.strftime("%A")
                dia = Config.DIAS_SEMANA.get(day_name, day_name)
            
            email = data['email']
            
            # Determinar si es entrada o salida consultando la tabla de estados
            cursor.execute("SELECT estado FROM estado_usuarios WHERE email = %s", (email,))
            estado_actual = cursor.fetchone()
            
            if estado_actual and estado_actual['estado'] == 'dentro':
                tipo = 'Salida'
                nuevo_estado = 'fuera'
            else:
                tipo = 'Entrada'
                nuevo_estado = 'dentro'
            
            # Insertar registro
            query = """
                INSERT INTO registros 
                (fecha, hora, dia, nombre, apellido, email, tipo, timestamp) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                fecha, hora, dia,
                data['nombre'], data['apellido'], email,
                tipo, timestamp
            ))
            
            # Actualizar el estado del usuario
            cursor.execute("""
                INSERT INTO estado_usuarios (email, nombre, apellido, estado, 
                    ultima_entrada, ultima_salida)
                VALUES (%s, %s, %s, %s, 
                    CASE WHEN %s = 'dentro' THEN NOW() ELSE NULL END,
                    CASE WHEN %s = 'fuera' THEN NOW() ELSE NULL END)
                ON DUPLICATE KEY UPDATE 
                    estado = %s, 
                    ultima_entrada = CASE WHEN %s = 'dentro' THEN NOW() ELSE ultima_entrada END,
                    ultima_salida = CASE WHEN %s = 'fuera' THEN NOW() ELSE ultima_salida END
            """, (
                email, data['nombre'], data['apellido'], nuevo_estado, 
                nuevo_estado, nuevo_estado,
                nuevo_estado, nuevo_estado, nuevo_estado
            ))
            
            conn.commit()
            registro_id = cursor.lastrowid
            
        conn.close()
        return jsonify({
            "message": "Registro agregado correctamente", 
            "id": registro_id,
            "tipo": tipo,
            "estado": nuevo_estado
        })
    except Exception as e:
        print(f"Error al añadir registro: {str(e)}")
        return jsonify({"error": str(e)}), 500