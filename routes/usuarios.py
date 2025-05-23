from flask import Blueprint, jsonify
from datetime import datetime, date, timedelta
from database import get_connection
from utils.datetime_utils import get_current_datetime

usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/usuarios', methods=['GET'])
def get_usuarios():
    """Obtener lista de usuarios permitidos activos"""
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios_permitidos WHERE activo = 1")
            usuarios = cursor.fetchall()
        conn.close()
        return jsonify(usuarios)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@usuarios_bp.route('/ayudantes_presentes', methods=['GET'])
def get_ayudantes_presentes():
    """Obtener ayudantes que están actualmente presentes"""
    try:
        conn = get_connection()
        
        with conn.cursor() as cursor:
            now = get_current_datetime()
            today = now.strftime('%Y-%m-%d')
            
            # Buscar ayudantes basados en la tabla registros
            # Un ayudante está presente si su último registro del día es de tipo 'Entrada'
            cursor.execute("""
                SELECT r.email, r.nombre, r.apellido, r.hora as ultima_entrada, u.foto_url
                FROM registros r
                JOIN (
                    -- Subconsulta para obtener el ID del último registro de cada usuario en el día actual
                    SELECT email, MAX(id) as last_id
                    FROM registros
                    WHERE fecha = %s
                    GROUP BY email
                ) as ultimos
                ON r.id = ultimos.last_id
                LEFT JOIN usuarios_permitidos u ON r.email = u.email
                WHERE r.fecha = %s
                AND r.tipo = 'Entrada'  -- Solo considerar como presentes a quienes su último registro sea Entrada
                ORDER BY r.hora DESC
            """, (today, today))
            
            ayudantes_dentro = cursor.fetchall()
            
            # Formateo de datos
            for ayudante in ayudantes_dentro:
                ayudante['estado'] = 'dentro'
                
                # Convertir tipos de datos
                for key, value in list(ayudante.items()):
                    if isinstance(value, (datetime, date)):
                        ayudante[key] = value.isoformat()
                    elif isinstance(value, timedelta):
                        ayudante[key] = str(value)
        
        conn.close()
        return jsonify(ayudantes_dentro)
    except Exception as e:
        print(f"Error al obtener ayudantes presentes: {str(e)}")
        return jsonify({"error": str(e)}), 500