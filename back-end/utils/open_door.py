#!/usr/bin/env python3
"""
Script standalone para abrir la puerta vía ESPHome.
Este script ha sido probado y funciona correctamente.
"""
import asyncio
import sys
from aioesphomeapi import APIClient
from config import Config

async def main():
    """Conecta a ESPHome y presiona el botón 'abrir'"""
    HOST = Config.DOOR_HOST
    PORT = Config.DOOR_PORT
    DEVICE_NAME = Config.DOOR_DEVICE_NAME
    API_KEY = Config.DOOR_API_KEY

    if not HOST or not API_KEY:
        print("❌ Error: ESPHOME_HOST o ESPHOME_TOKEN no configurados", file=sys.stderr)
        sys.exit(1)

    try:
        print(f"🔌 Conectando a ESPHome: {HOST}:{PORT} (device: {DEVICE_NAME})")
        client = APIClient(HOST, PORT, DEVICE_NAME, noise_psk=API_KEY)
        await client.connect(login=True)
        print("✅ Conectado a ESPHome")

        # Listar entidades y buscar el botón 'abrir'
        entities, _ = await client.list_entities_services()
        abrir_button = None
        for ent in entities:
            if ent.name and ent.name.lower() == "abrir":
                abrir_button = ent
                break

        if abrir_button is None:
            print("❌ No se encontró el botón 'Abrir'", file=sys.stderr)
            await client.disconnect()
            sys.exit(1)

        print(f"✅ Botón encontrado: {abrir_button.name}")

        # Presionar el botón (sin await, como en el script que funciona)
        client.button_command(abrir_button.key)
        print("🚪 Comando de apertura enviado")

        # Esperar un momento para que se envíe el comando
        await asyncio.sleep(0.5)

        await client.disconnect()
        print("✅ Puerta abierta exitosamente")
        sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
