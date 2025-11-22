import os
import ssl
from flask import Flask
from flask_cors import CORS
from pathlib import Path
from dotenv import load_dotenv
from database import get_connection

# Importar configuraciones y utilidades
from config import Config
from utils.json_encoder import CustomJSONProvider

# Importar blueprints de rutas
from routes.auth import auth_bp
from routes.registros import registros_bp
from routes.usuarios import usuarios_bp
from routes.horarios import horarios_bp
from routes.cumplimiento import cumplimiento_bp
from routes.horas import horas_bp
from routes.estado import estado_bp
from routes.lector import lector_bp

# Importar nuevos blueprints de estudiantes
from routes.estudiantes import estudiantes_bp
from routes.qr import qr_bp
from routes.registros_estudiantes import registros_estudiantes_bp

# Importar tareas programadas
from tasks.scheduled_tasks import configurar_tarea_cierre_diario, configurar_reinicio_semanal

# Cargar variables de entorno (.env si existe, si no .env.example)
base_path = Path(__file__).parent
env_path = base_path / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv(dotenv_path=base_path / '.env.example')

def create_app():
    """Factory function para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Configuración
    app.config.from_object(Config)
    
    # CORS - Configuración desde variable de entorno
    CORS(app, resources={
        r"/api/*": {
            "origins": Config.CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Configurar JSON encoder personalizado
    app.json_provider_class = CustomJSONProvider
    app.json = CustomJSONProvider(app)
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(registros_bp, url_prefix='/api')
    app.register_blueprint(usuarios_bp, url_prefix='/api')
    app.register_blueprint(horarios_bp, url_prefix='/api')
    app.register_blueprint(cumplimiento_bp, url_prefix='/api')
    app.register_blueprint(horas_bp, url_prefix='/api')
    app.register_blueprint(estado_bp, url_prefix='/api')
    app.register_blueprint(lector_bp, url_prefix='/api')
    ensure_estado_table()

    # Registrar blueprints de estudiantes
    app.register_blueprint(estudiantes_bp, url_prefix='/api/estudiantes')
    app.register_blueprint(qr_bp, url_prefix='/api')
    app.register_blueprint(registros_estudiantes_bp, url_prefix='/api/estudiantes')

    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        from datetime import datetime
        return {
            'status': 'OK',
            'timestamp': datetime.now().isoformat(),
            'message': 'API unificada funcionando correctamente',
            'services': ['ayudantes', 'estudiantes', 'qr', 'registros']
        }
    
    return app

def ensure_estado_table():
    """Crea la tabla estado_usuarios si no existe."""
    ddl = """
    CREATE TABLE IF NOT EXISTS estado_usuarios (
        email VARCHAR(100) NOT NULL PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        apellido VARCHAR(100) NOT NULL,
        estado ENUM('dentro', 'fuera') DEFAULT 'fuera',
        ultima_entrada DATETIME NULL,
        ultima_salida DATETIME NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(ddl)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"ADVERTENCIA: no se pudo asegurar la tabla estado_usuarios: {e}")

# Crear la aplicación
app = create_app()

if __name__ == '__main__':
    # Configurar tareas programadas
    try:
        import apscheduler
        configurar_tarea_cierre_diario()
        configurar_reinicio_semanal()
        print("Tareas programadas configuradas correctamente:")
        print("- Cierre automático: diariamente a las 23:59")
        print("- Reinicio semanal: domingos a las 23:55")
    except ImportError:
        print("ADVERTENCIA: No se pudieron configurar las tareas programadas.")
        print("Instale 'apscheduler' con: pip install apscheduler")
    
    # Configurar SSL solo si están disponibles los certificados
    cert_path = 'certificate.pem'
    key_path = 'privatekey.pem'
    use_ssl = os.getenv('USE_SSL', 'true').lower() == 'true'

    if use_ssl and os.path.exists(cert_path) and os.path.exists(key_path):
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(cert_path, key_path)
            context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
            print("Contexto SSL configurado correctamente")
            print("Iniciando servidor HTTPS en 0.0.0.0:5000")
            app.run(debug=True, host='0.0.0.0', port=5000, ssl_context=context)
        except Exception as e:
            print(f"Error al configurar SSL: {str(e)}")
            print("Iniciando servidor HTTP en 0.0.0.0:5000")
            app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Certificados SSL no encontrados o deshabilitados")
        print("Iniciando servidor HTTP en 0.0.0.0:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
