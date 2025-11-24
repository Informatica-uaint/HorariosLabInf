#!/usr/bin/env python3
"""
Script standalone para abrir la puerta vía ESPHome.
Este script ha sido probado y funciona correctamente.
"""
import asyncio
import os
import sys
from aioesphomeapi import APIClient

# Leer configuración de variables de entorno
HOST = os.getenv('ESPHOME_HOST', '10.0.5.5')
PORT = int(os.getenv('ESPHOME_PORT', '6053'))
DEVICE_NAME = os.getenv('ESPHOME_DEVICE_NAME', 'arturito')
API_KEY = os.getenv('ESPHOME_TOKEN')

async def main():
    try:
        print(f"🔧 Conectando a ESPHome: {HOST}:{PORT} (device: {DEVICE_NAME})")

        client = APIClient(HOST, PORT, DEVICE_NAME, noise_psk=API_KEY)

        # Intentar conectar con timeout
        print("🔌 Iniciando conexión...")
        await asyncio.wait_for(client.connect(login=True), timeout=10.0)
        print("✅ Conexión establecida")

        print("📋 Listando entidades...")
        entities, _ = await asyncio.wait_for(client.list_entities_services(), timeout=5.0)

        abrir_button = None
        for ent in entities:
            if ent.name.lower() == "abrir":
                abrir_button = ent
                break

        if abrir_button is None:
            print("❌ No se encontró el botón 'Abrir'")
            sys.exit(1)
        else:
            print(f"✅ Botón encontrado: {abrir_button.name} (key: {abrir_button.key})")
            # ❌ antes:
            # await client.button_command(abrir_button.key)
            # ✅ ahora:
            client.button_command(abrir_button.key)
            print("🚪 Comando de apertura enviado")
            # opcional: darle tiempo a que se envíe el comando
            await asyncio.sleep(0.5)

        print("🔌 Desconectando...")
        await client.disconnect()
        print("✅ Desconectado correctamente")

    except asyncio.TimeoutError as e:
        print(f"❌ Timeout: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrumpido por usuario")
        sys.exit(130)