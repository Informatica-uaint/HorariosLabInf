import subprocess
import sys
import os
from pathlib import Path
from config import Config
from database import get_connection


def open_door_if_authorized(user_email: str, user_type: str):
    """
    Determina si se debe abrir la puerta y retorna el resultado.

    Lógica:
    - AYUDANTE: Siempre autorizado
    - ESTUDIANTE: Autorizado solo si hay >= 2 ayudantes dentro

    Returns:
        dict: {"opened": bool, "authorized": bool, "message": str, "assistants_count": int}
    """
    # Debug: Mostrar valores de configuración
    print(f"🔧 DEBUG Config: DOOR_HOST={Config.DOOR_HOST}, DOOR_PORT={Config.DOOR_PORT}")
    print(f"🔧 DEBUG Config: DOOR_DEVICE_NAME={Config.DOOR_DEVICE_NAME}, DOOR_API_KEY={'SET' if Config.DOOR_API_KEY else 'NOT SET'}")

    if not Config.DOOR_HOST or not Config.DOOR_API_KEY:
        # Config incompleta, pero no lanzar excepción - solo retornar que no se abrió
        print(f"⚠️  Config incompleta: DOOR_HOST={Config.DOOR_HOST is not None}, DOOR_API_KEY={Config.DOOR_API_KEY is not None}")
        return {
            "opened": False,
            "authorized": False,
            "message": "Configuración de puerta incompleta",
            "assistants_count": 0
        }

    user_type = (user_type or '').upper()
    authorized = False
    assistants_count = 0
    message = ""

    if user_type == 'AYUDANTE':
        authorized = True
        message = "Acceso autorizado - Ayudante"
    elif user_type == 'ESTUDIANTE':
        # Contar ayudantes dentro usando la tabla registros (como generador-qr)
        from utils.datetime_utils import get_current_datetime
        conn = get_connection()

        try:
            with conn.cursor() as cursor:
                now = get_current_datetime()
                today = now.strftime('%Y-%m-%d')

                # Obtener todos los registros de ayudantes del día
                cursor.execute("""
                    SELECT email, tipo, hora
                    FROM registros
                    WHERE fecha = %s
                    ORDER BY hora ASC
                """, (today,))

                registros = cursor.fetchall()

                # Agrupar por email y determinar último estado
                ayudantes_status = {}
                for registro in registros:
                    ayudantes_status[registro['email']] = registro['tipo']

                # Contar ayudantes con último registro = 'Entrada'
                assistants_count = sum(1 for tipo in ayudantes_status.values() if tipo == 'Entrada')
        finally:
            conn.close()

        authorized = assistants_count >= 2

        if authorized:
            message = f"Acceso autorizado - {assistants_count} ayudantes dentro"
        else:
            message = "Toca el timbre"
    else:
        authorized = False
        message = "Tipo de usuario no válido"

    # Intentar abrir la puerta si está autorizado
    door_opened = False
    if authorized:
        try:
            print("🔓 Ejecutando script de apertura de puerta...")

            # Ejecutar script standalone que está probado y funciona
            # Pasar explícitamente las variables de entorno
            script_path = Path(__file__).parent / 'open_door.py'

            # Preparar environment con variables necesarias
            env = os.environ.copy()
            env['ESPHOME_HOST'] = Config.DOOR_HOST
            env['ESPHOME_PORT'] = str(Config.DOOR_PORT)
            env['ESPHOME_DEVICE_NAME'] = Config.DOOR_DEVICE_NAME
            if Config.DOOR_API_KEY:
                env['ESPHOME_TOKEN'] = Config.DOOR_API_KEY

            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=15,  # Aumentar timeout a 15 segundos
                env=env
            )

            if result.returncode == 0:
                door_opened = True
                print(f"✅ Puerta abierta exitosamente")
                print(f"   Output: {result.stdout.strip()}")
            else:
                door_opened = False
                error_msg = result.stderr.strip() or result.stdout.strip()
                message = f"Error al abrir puerta: {error_msg}"
                print(f"❌ {message}")
                if result.stdout:
                    print(f"   Stdout: {result.stdout.strip()}")
                if result.stderr:
                    print(f"   Stderr: {result.stderr.strip()}")

        except subprocess.TimeoutExpired:
            door_opened = False
            message = "Error al abrir puerta: Timeout después de 15 segundos"
            print(f"❌ {message}")
        except Exception as e:
            door_opened = False
            message = f"Error al abrir puerta: {str(e)}"
            print(f"❌ Excepción: {message}")

    return {
        "opened": door_opened,
        "authorized": authorized,
        "message": message,
        "assistants_count": assistants_count
    }
