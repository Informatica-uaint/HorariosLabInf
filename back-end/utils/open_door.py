#!/usr/bin/env python3
"""
Script standalone para abrir la puerta vía ESPHome.
Este script ha sido probado y funciona correctamente.
"""
import asyncio
import os
from aioesphomeapi import APIClient

# Leer configuración de variables de entorno
HOST = os.getenv('ESPHOME_HOST', '10.0.5.5')
PORT = int(os.getenv('ESPHOME_PORT', '6053'))
DEVICE_NAME = os.getenv('ESPHOME_DEVICE_NAME', 'arturito')
API_KEY = os.getenv('ESPHOME_TOKEN')

async def main():
    client = APIClient(HOST, PORT, DEVICE_NAME, noise_psk=API_KEY)
    await client.connect(login=True)

    entities, _ = await client.list_entities_services()
    abrir_button = None
    for ent in entities:
        if ent.name.lower() == "abrir":
            abrir_button = ent
            break

    if abrir_button is None:
        print("❌ No se encontró el botón 'Abrir'")
    else:
        print(f"✅ Botón encontrado: {abrir_button}")
        # ❌ antes:
        # await client.button_command(abrir_button.key)
        # ✅ ahora:
        client.button_command(abrir_button.key)
        # opcional: darle tiempo a que se envíe el comando
        await asyncio.sleep(0.5)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())