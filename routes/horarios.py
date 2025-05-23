from flask import Blueprint, jsonify
from database import get_connection

horarios_bp = Blueprint('horarios', __name__)

@horarios_bp.route('/horarios', methods=['GET'])
def get_horarios():
    """Obtener todos los horarios asignados a usuarios"""
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            query = """
                SELECT h.id, h.usuario_id, u.nombre, u.apellido, u.email, 
                       h.dia, h.hora_entrada, h.hora_salida
                FROM horarios_asignados h
                JOIN usuarios_permitidos u ON h.usuario_id = u.id
            """
            cursor.execute(query)
            horarios = cursor.fetchall()
        conn.close()
        return jsonify(horarios)
    except Exception as e:
        return jsonify({"error": str(e)}), 500