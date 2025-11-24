import asyncio
from aioesphomeapi import APIClient, ButtonInfo
from config import Config
from database import get_connection


async def _press_button(host, port, device_name, api_key, button_name='abrir'):
    client = APIClient(host, port, device_name, noise_psk=api_key)
    await client.connect(login=True)
    entities, _ = await client.list_entities_services()
    target = None
    for ent in entities:
        if isinstance(ent, ButtonInfo) and ent.name and ent.name.lower() == button_name.lower():
            target = ent
            break
    if not target:
        await client.disconnect()
        raise RuntimeError(f"No se encontró el botón '{button_name}'")
    # Ejecutar comando
    await client.button_command(target.key)
    await asyncio.sleep(0.5)
    await client.disconnect()


def open_door_if_authorized(user_email: str, user_type: str):
    """
    Determina si se debe abrir la puerta y retorna el resultado.

    Lógica:
    - AYUDANTE: Siempre autorizado
    - ESTUDIANTE: Autorizado solo si hay >= 2 ayudantes dentro

    Returns:
        dict: {"opened": bool, "authorized": bool, "message": str, "assistants_count": int}
    """
    if not Config.DOOR_HOST or not Config.DOOR_API_KEY:
        # Config incompleta, pero no lanzar excepción - solo retornar que no se abrió
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
            asyncio.run(
                _press_button(
                    Config.DOOR_HOST,
                    Config.DOOR_PORT,
                    Config.DOOR_DEVICE_NAME,
                    Config.DOOR_API_KEY
                )
            )
            door_opened = True
        except Exception as e:
            message = f"Error al abrir puerta: {str(e)}"
            door_opened = False

    return {
        "opened": door_opened,
        "authorized": authorized,
        "message": message,
        "assistants_count": assistants_count
    }
