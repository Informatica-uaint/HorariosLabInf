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
    client.button_command(target.key)
    await asyncio.sleep(0.5)
    await client.disconnect()


def open_door_if_authorized(user_email: str, user_type: str):
    """
    Abre la puerta sólo si:
    - user_type == 'AYUDANTE'
    - user_type == 'ESTUDIANTE' y hay al menos 2 ayudantes dentro (estado_usuarios.estado = 'dentro')
    """
    if not Config.DOOR_HOST or not Config.DOOR_API_KEY:
        raise RuntimeError("Config de puerta incompleta: defina DOOR_HOST y DOOR_API_KEY")

    user_type = (user_type or '').upper()
    if user_type == 'AYUDANTE':
        authorized = True
    elif user_type == 'ESTUDIANTE':
        # Verificar ayudantes dentro
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as cnt 
                FROM estado_usuarios eu
                JOIN usuarios_permitidos up ON up.email = eu.email
                WHERE eu.estado = 'dentro' AND up.activo = 1
            """)
            row = cursor.fetchone()
        conn.close()
        authorized = row and row['cnt'] >= 2
    else:
        authorized = False

    if not authorized:
        raise PermissionError("Apertura no autorizada para este usuario")

    asyncio.run(
        _press_button(
            Config.DOOR_HOST,
            Config.DOOR_PORT,
            Config.DOOR_DEVICE_NAME,
            Config.DOOR_API_KEY
        )
    )
