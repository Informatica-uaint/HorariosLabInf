import os
from flask import Blueprint, request, jsonify
from datetime import datetime
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from database import get_connection
from utils.datetime_utils import get_current_datetime
from config import Config

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

            cursor.execute("""
                INSERT INTO registros (fecha, hora, dia, nombre, apellido, email, tipo, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                fecha, hora, dia, nombre, apellido, email, tipo, now
            ))

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

        return jsonify({
            "success": True,
            "message": "Acceso registrado",
            "tipo": tipo,
            "estado": nuevo_estado,
            "registro_id": registro_id,
            "station_id": station_id,
            "nonce": nonce
        })
    except Exception as exc:
        print(f"Error en validar_token_lector: {str(exc)}")
        return jsonify({"error": "Error interno", "detail": str(exc)}), 500
