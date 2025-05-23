import os
import ssl
from flask import Flask
from flask_cors import CORS
from pathlib import Path
from dotenv import load_dotenv

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

# Importar tareas programadas
from tasks.scheduled_tasks import configurar_tarea_cierre_diario, configurar_reinicio_semanal

# Cargar variables de entorno
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

def create_app():
    """Factory function para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Configuración
    app.config.from_object(Config)
    
    # CORS
    CORS(app)
    
    # Configurar JSON encoder personalizado
    app.json_provider_class = CustomJSONProvider
    app.json = CustomJSONProvider(app)
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(registros_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(horarios_bp)
    app.register_blueprint(cumplimiento_bp)
    app.register_blueprint(horas_bp)
    app.register_blueprint(estado_bp)
    
    return app

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
    
    # Configurar SSL
    cert_path = 'certificate.pem'
    key_path = 'privatekey.pem'
    
    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        print(f"Error: Certificados no encontrados")
        print(f"Certificado: {cert_path}")
        print(f"Clave privada: {key_path}")
        exit(1)
    
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_path, key_path)
        context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        print("Contexto SSL configurado correctamente")
    except Exception as e:
        print(f"Error al configurar SSL: {str(e)}")
        exit(1)
    
    print("Iniciando servidor HTTPS en 0.0.0.0:5000")
    app.run(debug=True, host='0.0.0.0', port=5000, ssl_context=context)