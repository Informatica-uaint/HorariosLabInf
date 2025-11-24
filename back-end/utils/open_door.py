#!/usr/bin/env python3
"""
Script standalone para abrir la puerta vía ESPHome.
Este script ha sido probado y funciona correctamente.

Usage: python open_door.py <host> <port> <device_name> <api_key>
"""
import asyncio
import sys
from aioesphomeapi import APIClient

async def main(host, port, device_name, api_key):
    """Conecta a ESPHome y presiona el botón 'abrir'"""
    if not host or not api_key:
        print("❌ Error: Host o API key no proporcionados", file=sys.stderr)
        sys.exit(1)

    try:
        print(f"🔌 Conectando a ESPHome: {host}:{port} (device: {device_name})")
        client = APIClient(host, port, device_name, noise_psk=api_key)
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
    if len(sys.argv) != 5:
        print("Usage: python open_door.py <host> <port> <device_name> <api_key>", file=sys.stderr)
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    device_name = sys.argv[3]
    api_key = sys.argv[4]

    asyncio.run(main(host, port, device_name, api_key))
