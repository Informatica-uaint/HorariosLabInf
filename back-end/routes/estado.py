from flask import Blueprint, request, jsonify
from datetime import datetime
from database import get_connection
from utils.datetime_utils import get_current_datetime
from config import Config

estado_bp = Blueprint('estado', __name__)

@estado_bp.route('/estado_usuarios', methods=['GET'])
def get_estados_usuarios():
    """Obtener estados de todos los usuarios"""
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT e.*, u.foto_url
                FROM estado_usuarios e
                LEFT JOIN usuarios_permitidos u ON e.email = u.email
                ORDER BY e.updated_at DESC
            """)
            estados = cursor.fetchall()
            
            # Convertir datetime a strings
            for estado in estados:
                for key, value in estado.items():
                    if isinstance(value, datetime):
                        estado[key] = value.isoformat()
        
        conn.close()
        return jsonify(estados)
    except Exception as e:
        print(f"Error obteniendo estados de usuarios: {str(e)}")
        return jsonify({"error": str(e)}), 500

@estado_bp.route('/estado_usuario/<email>', methods=['PUT'])
def update_estado_usuario(email):
    """Actualizar estado de un usuario específico"""
    try:
        data = request.get_json()
        estado = data.get('estado', 'fuera')
        
        conn = get_connection()
        with conn.cursor() as cursor:
            # Verificar si el usuario ya existe en la tabla
            cursor.execute("SELECT * FROM estado_usuarios WHERE email = %s", (email,))
            existente = cursor.fetchone()
            
            if existente:
                # Actualizar el registro existente
                cursor.execute("""
                    UPDATE estado_usuarios 
                    SET estado = %s, 
                        ultima_entrada = CASE WHEN %s = 'dentro' THEN NOW() ELSE ultima_entrada END,
                        ultima_salida = CASE WHEN %s = 'fuera' THEN NOW() ELSE ultima_salida END
                    WHERE email = %s
                """, (estado, estado, estado, email))
            else:
                # Buscar información del usuario
                cursor.execute("SELECT nombre, apellido FROM usuarios_permitidos WHERE email = %s", (email,))
                usuario = cursor.fetchone()
                if not usuario:
                    return jsonify({"error": "Usuario no encontrado"}), 404
                
                # Crear un nuevo registro
                cursor.execute("""
                    INSERT INTO estado_usuarios (email, nombre, apellido, estado, 
                        ultima_entrada, ultima_salida)
                    VALUES (%s, %s, %s, %s, 
                        CASE WHEN %s = 'dentro' THEN NOW() ELSE NULL END,
                        CASE WHEN %s = 'fuera' THEN NOW() ELSE NULL END)
                """, (email, usuario['nombre'], usuario['apellido'], estado, estado, estado))
            
            conn.commit()
        conn.close()
        return jsonify({"message": f"Estado de usuario actualizado a '{estado}'"})
    except Exception as e:
        print(f"Error actualizando estado de usuario: {str(e)}")
        return jsonify({"error": str(e)}), 500

@estado_bp.route('/procesar_salidas_pendientes', methods=['POST'])
def procesar_salidas_pendientes():
    """Procesar salidas pendientes al final del día"""
    try:
        conn = get_connection()
        registros_procesados = []
        
        with conn.cursor() as cursor:
            # Obtener fecha y hora actual
            now = get_current_datetime()
            fecha = now.strftime("%Y-%m-%d")
            hora = now.strftime("%H:%M:%S")
            
            # Día de la semana en español
            dia = Config.DIAS_SEMANA.get(now.strftime("%A"), now.strftime("%A"))
            
            # 1. Buscar usuarios que tienen registros de entrada sin salida correspondiente HOY
            cursor.execute("""
                SELECT u.email, u.nombre, u.apellido, MAX(r.id) as ultimo_id, MAX(r.hora) as ultima_hora
                FROM usuarios_permitidos u
                JOIN registros r ON u.email = r.email
                WHERE r.fecha = %s AND r.tipo = 'Entrada'
                AND NOT EXISTS (
                    SELECT 1 FROM registros r2 
                    WHERE r2.email = r.email 
                    AND r2.fecha = r.fecha 
                    AND r2.tipo = 'Salida'
                    AND r2.id > r.id
                )
                GROUP BY u.email, u.nombre, u.apellido
            """, (fecha,))
            
            usuarios_sin_salida = cursor.fetchall()
            
            # 2. También buscar usuarios con estado 'dentro' en la tabla estado_usuarios como respaldo
            cursor.execute("""
                SELECT e.email, e.nombre, e.apellido
                FROM estado_usuarios e
                JOIN usuarios_permitidos u ON e.email = u.email
                WHERE e.estado = 'dentro'
                AND NOT EXISTS (
                    SELECT 1 FROM registros r 
                    WHERE r.email = e.email 
                    AND r.fecha = %s
                    AND r.tipo = 'Salida'
                )
            """, (fecha,))
            
            usuarios_dentro = cursor.fetchall()
            
            # Combinar ambos conjuntos de usuarios
            emails_procesados = set()
            todos_usuarios = []
            
            # Primero añadir usuarios con registros de entrada sin salida
            for usuario in usuarios_sin_salida:
                if usuario['email'] not in emails_procesados:
                    todos_usuarios.append(usuario)
                    emails_procesados.add(usuario['email'])
            
            # Luego añadir usuarios con estado 'dentro' sin registro de salida
            for usuario in usuarios_dentro:
                if usuario['email'] not in emails_procesados:
                    todos_usuarios.append(usuario)
                    emails_procesados.add(usuario['email'])
            
            # Procesar cada usuario
            for usuario in todos_usuarios:
                # Insertar registro de salida automático
                cursor.execute("""
                    INSERT INTO registros 
                    (fecha, hora, dia, nombre, apellido, email, tipo, auto_generado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    fecha,
                    hora,
                    dia,
                    usuario['nombre'],
                    usuario['apellido'],
                    usuario['email'],
                    'Salida',
                    True  # Marcar como auto-generado
                ))
                
                # Actualizar estado a 'fuera'
                cursor.execute("""
                    UPDATE estado_usuarios 
                    SET estado = 'fuera', ultima_salida = NOW()
                    WHERE email = %s
                """, (usuario['email'],))
                
                registros_procesados.append({
                    'email': usuario['email'],
                    'nombre': usuario['nombre'],
                    'apellido': usuario['apellido'],
                    'fecha': fecha,
                    'hora': hora
                })
            
            # Confirmar los cambios
            conn.commit()
            
        conn.close()
        
        return jsonify({
            'fecha_procesada': fecha,
            'registros_creados': len(registros_procesados),
            'detalle': registros_procesados
        })
    
    except Exception as e:
        print(f"Error al procesar salidas pendientes: {str(e)}")
        return jsonify({"error": str(e)}), 500