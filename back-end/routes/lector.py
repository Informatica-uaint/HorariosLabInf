import os
from flask import Blueprint, request, jsonify
from datetime import datetime
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from database import get_connection
from utils.datetime_utils import get_current_datetime
from config import Config
from utils.door_control import open_door_if_authorized

lector_bp = Blueprint('lector', __name__)

READER_QR_SECRET = os.getenv('READER_QR_SECRET', Config.READER_QR_SECRET)
READER_STATION_ID = os.getenv('READER_STATION_ID', Config.READER_STATION_ID)


@lector_bp.route('/lector/validar', methods=['POST'])
def validar_token_lector():
    """Valida un token QR emitido por el lector y registra entrada/salida del usuario autenticado."""
    data = request.get_json() or {}
    token = data.get('token')
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    email = data.get('email')

    if not token or not nombre or not apellido or not email:
        return jsonify({"error": "token, nombre, apellido y email son requeridos"}), 400

    if not READER_QR_SECRET:
        return jsonify({"error": "Servidor no configurado: falta READER_QR_SECRET"}), 500

    try:
        payload = jwt.decode(token, READER_QR_SECRET, algorithms=['HS256'])
    except ExpiredSignatureError:
        return jsonify({"error": "QR expirado", "reason": "expired"}), 401
    except InvalidTokenError as exc:
        return jsonify({"error": "QR inválido", "reason": str(exc)}), 400

    station_id = payload.get('station_id', READER_STATION_ID)
    nonce = payload.get('nonce')
    user_type = ''  # Inicializar para uso posterior en door_control

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            now = get_current_datetime()
            fecha = now.strftime("%Y-%m-%d")
            hora = now.strftime("%H:%M:%S")
            dia = Config.DIAS_SEMANA.get(now.strftime("%A"), now.strftime("%A"))

            cursor.execute("SELECT estado FROM estado_usuarios WHERE email = %s", (email,))
            estado_actual = cursor.fetchone()

            if estado_actual and estado_actual['estado'] == 'dentro':
                tipo = 'Salida'
                nuevo_estado = 'fuera'
            else:
                tipo = 'Entrada'
                nuevo_estado = 'dentro'

            # Determinar tipo de usuario (ayudante vs estudiante)
            cursor.execute("SELECT id FROM usuarios_permitidos WHERE email = %s AND TP = 'AYUDANTE'", (email,))
            is_assistant = cursor.fetchone() is not None

            cursor.execute("SELECT id FROM usuarios_estudiantes WHERE email = %s", (email,))
            is_student = cursor.fetchone() is not None

            # Guardar tipo de usuario para control de puerta
            if is_assistant:
                user_type = 'AYUDANTE'
            elif is_student:
                user_type = 'ESTUDIANTE'
            else:
                user_type = ''

            # Insertar en la tabla correcta según el tipo de usuario
            if is_assistant:
                # Insertar en tabla de ayudantes (registros)
                cursor.execute("""
                    INSERT INTO registros (fecha, hora, dia, nombre, apellido, email, tipo, auto_generado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
                """, (
                    fecha, hora, dia, nombre, apellido, email, tipo
                ))
            elif is_student:
                # Insertar en tabla de estudiantes (EST_registros)
                cursor.execute("""
                    INSERT INTO EST_registros (fecha, hora, dia, nombre, apellido, email, tipo, auto_generado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
                """, (
                    fecha, hora, dia, nombre, apellido, email, tipo
                ))
            else:
                # Usuario no encontrado en ninguna tabla
                conn.close()
                return jsonify({"error": "Usuario no autorizado", "reason": "not_found"}), 403

            cursor.execute("""
                INSERT INTO estado_usuarios (email, nombre, apellido, estado, ultima_entrada, ultima_salida)
                VALUES (%s, %s, %s, %s,
                    CASE WHEN %s = 'dentro' THEN NOW() ELSE NULL END,
                    CASE WHEN %s = 'fuera' THEN NOW() ELSE NULL END)
                ON DUPLICATE KEY UPDATE 
                    estado = %s, 
                    ultima_entrada = CASE WHEN %s = 'dentro' THEN NOW() ELSE ultima_entrada END,
                    ultima_salida = CASE WHEN %s = 'fuera' THEN NOW() ELSE ultima_salida END
            """, (
                email, nombre, apellido, nuevo_estado,
                nuevo_estado, nuevo_estado,
                nuevo_estado, nuevo_estado, nuevo_estado
            ))

            conn.commit()
            registro_id = cursor.lastrowid

        conn.close()

        response = {
            "success": True,
            "message": "Acceso registrado",
            "tipo": tipo,
            "estado": nuevo_estado,
            "registro_id": registro_id,
            "station_id": station_id,
            "nonce": nonce
        }
    except Exception as exc:
        print(f"Error en validar_token_lector: {str(exc)}")
        return jsonify({"error": "Error interno", "detail": str(exc)}), 500

    # Intentar apertura de puerta según tipo de usuario
    print(f"🚪 DEBUG: Intentando abrir puerta - user_type='{user_type}', email='{email}'")
    door_result = None
    try:
        door_result = open_door_if_authorized(email, user_type)
        print(f"🚪 DEBUG: Resultado door_control: {door_result}")
        # Agregar información de la puerta a la respuesta
        response['door_opened'] = door_result.get('opened', False)
        response['door_authorized'] = door_result.get('authorized', False)
        response['door_message'] = door_result.get('message', '')
        if door_result.get('assistants_count') is not None:
            response['assistants_inside'] = door_result.get('assistants_count')
    except Exception as e:
        print(f"Error al procesar apertura de puerta: {e}")
        response['door_opened'] = False
        response['door_message'] = f"Error: {str(e)}"

    return jsonify(response)
