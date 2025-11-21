from flask import Blueprint, request, jsonify
from database import get_connection
from utils.auth import hash_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Registrar nuevo usuario administrador"""
    data = request.get_json() or {}
    required = ['email', 'password', 'nombre', 'apellido']
    
    if not all(data.get(field) for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        hashed_pwd = hash_password(data['password'])
        conn = get_connection()
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM admin_users WHERE email = %s", (data['email'],))
            if cursor.fetchone():
                return jsonify({'error': 'Email already registered'}), 409

            cursor.execute(
                "INSERT INTO admin_users (nombre, apellido, email, password, role) VALUES (%s, %s, %s, %s, %s)",
                (data['nombre'], data['apellido'], data['email'], hashed_pwd, data.get('role', 'admin'))
            )
            conn.commit()
            user_id = cursor.lastrowid
            
        conn.close()
        return jsonify({'message': 'User registered successfully', 'id': user_id}), 201
        
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'error': 'Server error during registration'}), 500