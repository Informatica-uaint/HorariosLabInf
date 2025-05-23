import jwt
import hashlib
from functools import wraps
from flask import request, jsonify
from config import Config
from database import get_connection

def token_required(f):
    """Decorador para validar token JWT en endpoints protegidos"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token is missing!'}), 401

        token = auth_header.split(' ')[1]
        try:
            data = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM admin_users WHERE id = %s", (data['id'],))
                current_user = cursor.fetchone()
            conn.close()

            if not current_user:
                return jsonify({'error': 'Invalid token!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

def hash_password(password):
    """Hashea una contraseña usando SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()