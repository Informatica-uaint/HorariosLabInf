# -*- coding: utf-8 -*-
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.popup import Popup

import time
import json
from datetime import datetime
import threading
import sys
import requests
import urllib3
from pyzbar import pyzbar
from PIL import Image
import io

# Deshabilitar warnings SSL si es necesario
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurar ventana
Window.size = (600, 400)
Window.resizable = False

# Configuracion de la API para QR
API_CONFIG = {
    'base_url': 'https://acceso.informaticauaint.com/api-lector',
    'timeout': 15,
    'verify_ssl': False,
    'headers': {
        'Content-Type': 'application/json',
        'User-Agent': 'QR-Reader-Client/1.0',
        'Accept': 'application/json'
    }
}

# Colores para la interfaz
COLORS = {
    'primary': '#3498db',
    'success': '#2ecc71',
    'error': '#e74c3c',
    'warning': '#f39c12',
    'dark_bg': '#2c3e50',
    'light_text': '#ecf0f1',
    'accent': '#9b59b6',
    'button': '#3498db',
    'entry': '#27ae60',
    'exit': '#e67e22'
}

class BackgroundLayout(BoxLayout):
    """BoxLayout con fondo personalizado"""
    def __init__(self, bg_color=COLORS['dark_bg'], **kwargs):
        super(BackgroundLayout, self).__init__(**kwargs)
        self.bg_color = get_color_from_hex(bg_color)
        
        with self.canvas.before:
            Color(*self.bg_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self._update_rect, size=self._update_rect)
    
    def _update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

class QRReaderSimple(BackgroundLayout):
    def __init__(self, **kwargs):
        super(QRReaderSimple, self).__init__(bg_color=COLORS['dark_bg'], **kwargs)
        self.orientation = 'vertical'
        
        # Estado del sistema
        self.api_busy = False
        
        # Verificar conexión API
        self.api_connected = self.check_api_connection()
        
        # Configurar interfaz
        self.setup_ui()
        
        print("Lector QR Simple iniciado")
    
    def check_api_connection(self):
        """Verificar conexión con la API"""
        try:
            response = requests.get(
                API_CONFIG['base_url'] + '/health', 
                timeout=5,
                verify=API_CONFIG['verify_ssl'],
                headers=API_CONFIG['headers']
            )
            return response.status_code == 200
        except:
            return False
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        # Header con título
        header = BackgroundLayout(
            orientation='horizontal', 
            size_hint=(1, 0.15), 
            bg_color=COLORS['dark_bg'],
            padding=[10, 10]
        )
        
        title_label = Label(
            text="LECTOR QR - LABORATORIO INFORMÁTICA",
            font_size='16sp',
            bold=True,
            color=get_color_from_hex(COLORS['light_text'])
        )
        header.add_widget(title_label)
        self.add_widget(header)
        
        # Panel principal
        main_panel = BackgroundLayout(
            orientation='vertical',
            size_hint=(1, 0.7),
            bg_color=COLORS['dark_bg'], 
            padding=[20, 10], 
            spacing=15
        )
        
        # Estado del sistema
        if self.api_connected:
            status_text = "✓ API CONECTADA - LISTO PARA USAR"
            status_color = COLORS['success']
        else:
            status_text = "✗ API NO DISPONIBLE"
            status_color = COLORS['error']
            
        self.status_label = Label(
            text=status_text,
            font_size='14sp',
            bold=True,
            color=get_color_from_hex(status_color),
            size_hint=(1, 0.2)
        )
        main_panel.add_widget(self.status_label)
        
        # Instrucciones
        if self.api_connected:
            instructions = "Pegue el contenido del código QR en el campo de texto de abajo\ny presione 'PROCESAR QR' para registrar la asistencia."
        else:
            instructions = "No hay conexión con la API. Verifique su conexión a internet\ny presione 'RECONECTAR' para intentar nuevamente."
        
        instructions_label = Label(
            text=instructions,
            font_size='11sp',
            color=get_color_from_hex(COLORS['light_text']),
            size_hint=(1, 0.2),
            text_size=(None, None),
            halign='center'
        )
        main_panel.add_widget(instructions_label)
        
        # Campo de texto para QR
        qr_label = Label(
            text="Contenido del código QR:",
            font_size='12sp',
            color=get_color_from_hex(COLORS['light_text']),
            size_hint=(1, 0.1)
        )
        main_panel.add_widget(qr_label)
        
        self.qr_input = TextInput(
            multiline=True,
            size_hint=(1, 0.3),
            hint_text="Pegue aquí el contenido del código QR...",
            font_size='10sp'
        )
        main_panel.add_widget(self.qr_input)
        
        # Botones
        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.2),
            spacing=10
        )
        
        self.process_button = Button(
            text="PROCESAR QR",
            background_color=get_color_from_hex(COLORS['success']),
            color=get_color_from_hex(COLORS['light_text']),
            bold=True,
            disabled=not self.api_connected
        )
        self.process_button.bind(on_press=self.process_qr_text)
        
        clear_button = Button(
            text="LIMPIAR",
            background_color=get_color_from_hex(COLORS['warning']),
            color=get_color_from_hex(COLORS['light_text']),
            bold=True
        )
        clear_button.bind(on_press=self.clear_text)
        
        button_layout.add_widget(self.process_button)
        button_layout.add_widget(clear_button)
        main_panel.add_widget(button_layout)
        
        self.add_widget(main_panel)
        
        # Panel inferior - controles
        footer = BackgroundLayout(
            orientation='horizontal',
            size_hint=(1, 0.15),
            bg_color=COLORS['dark_bg'],
            padding=[10, 5],
            spacing=10
        )
        
        # Estado de conexión
        api_status_text = "API: " + ("CONECTADA" if self.api_connected else "ERROR")
        api_color = COLORS['success'] if self.api_connected else COLORS['error']
        
        self.api_status_label = Label(
            text=api_status_text,
            font_size='10sp',
            bold=True,
            color=get_color_from_hex(api_color),
            size_hint=(0.3, 1)
        )
        footer.add_widget(self.api_status_label)
        
        # Botón de reconectar
        reconnect_button = Button(
            text="RECONECTAR",
            background_color=get_color_from_hex(COLORS['accent']),
            color=get_color_from_hex(COLORS['light_text']),
            bold=True,
            size_hint=(0.35, 1)
        )
        reconnect_button.bind(on_press=self.reconnect_api)
        footer.add_widget(reconnect_button)
        
        # Botón de salir
        quit_button = Button(
            text="SALIR",
            background_color=get_color_from_hex(COLORS['error']),
            color=get_color_from_hex(COLORS['light_text']),
            bold=True,
            size_hint=(0.35, 1)
        )
        quit_button.bind(on_press=self.quit_app)
        footer.add_widget(quit_button)
        
        self.add_widget(footer)
    
    def clear_text(self, instance):
        """Limpiar campo de texto"""
        self.qr_input.text = ""
    
    def process_qr_text(self, instance):
        """Procesar texto del QR"""
        qr_text = self.qr_input.text.strip()
        if not qr_text:
            self.show_message("Error", "Por favor ingrese el contenido del código QR")
            return
        
        if not self.api_connected:
            self.show_message("Error", "No hay conexión con la API")
            return
        
        # Procesar en hilo separado
        self.process_qr_async(qr_text)
    
    def process_qr_async(self, qr_data):
        """Procesar QR en hilo separado"""
        if self.api_busy:
            return
        
        def process_thread():
            self.api_busy = True
            try:
                self.process_qr(qr_data)
            finally:
                self.api_busy = False
        
        thread = threading.Thread(target=process_thread)
        thread.daemon = True
        thread.start()
    
    def process_qr(self, qr_data):
        """Enviar QR a la API para procesamiento"""
        try:
            print(f"QR detectado: {qr_data[:50]}...")
            
            # Actualizar UI
            self.update_status("Procesando QR...")
            
            # Parsear QR data
            try:
                if isinstance(qr_data, str):
                    # Intentar parsear como JSON
                    try:
                        parsed_data = json.loads(qr_data)
                    except json.JSONDecodeError:
                        # Si no es JSON, enviar como string simple
                        parsed_data = {"qr_data": qr_data}
                else:
                    parsed_data = qr_data
            except Exception:
                self.show_message("Error", "Formato QR inválido")
                return
            
            # Enviar a API
            response = requests.post(
                API_CONFIG['base_url'] + '/validate-qr',
                json=parsed_data,
                timeout=API_CONFIG['timeout'],
                verify=API_CONFIG['verify_ssl'],
                headers=API_CONFIG['headers']
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success', False):
                    # Construir resultado exitoso
                    nombre = result.get('nombre', '')
                    apellido = result.get('apellido', '')
                    tipo = result.get('tipo', 'Registro')
                    message = result.get('message', 'Registro exitoso')
                    
                    success_msg = f"✓ REGISTRO EXITOSO\n\n{nombre} {apellido}\nTipo: {tipo}\n\n{message}"
                    self.show_message("Éxito", success_msg)
                    self.qr_input.text = ""  # Limpiar campo
                    
                else:
                    # Error desde API
                    error_msg = result.get('error', result.get('message', 'Error desconocido'))
                    self.show_message("Error", f"Error del servidor:\n{error_msg}")
            else:
                # Error HTTP
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', f'Error HTTP {response.status_code}')
                except:
                    error_msg = f'Error HTTP {response.status_code}'
                
                self.show_message("Error", f"Error de conexión:\n{error_msg}")
        
        except requests.exceptions.ConnectionError:
            self.api_connected = False
            self.update_api_status()
            self.show_message("Error", "Error de conexión.\nVerifique su conexión a internet.")
        except requests.exceptions.Timeout:
            self.show_message("Error", "Tiempo de espera agotado.\nLa API no responde.")
        except Exception as e:
            self.show_message("Error", f"Error inesperado:\n{str(e)[:100]}")
        finally:
            self.reset_status()
    
    def update_status(self, status_text):
        """Actualizar estado en UI"""
        self.status_label.text = status_text
        self.status_label.color = get_color_from_hex(COLORS['warning'])
        self.process_button.disabled = True
    
    def reset_status(self):
        """Restaurar estado inicial de la UI"""
        if self.api_connected:
            self.status_label.text = "✓ API CONECTADA - LISTO PARA USAR"
            self.status_label.color = get_color_from_hex(COLORS['success'])
            self.process_button.disabled = False
        else:
            self.status_label.text = "✗ API NO DISPONIBLE"
            self.status_label.color = get_color_from_hex(COLORS['error'])
            self.process_button.disabled = True
    
    def update_api_status(self):
        """Actualizar estado de conexión API"""
        api_status_text = "API: " + ("CONECTADA" if self.api_connected else "ERROR")
        api_color = COLORS['success'] if self.api_connected else COLORS['error']
        self.api_status_label.text = api_status_text
        self.api_status_label.color = get_color_from_hex(api_color)
        
        self.process_button.disabled = not self.api_connected
    
    def reconnect_api(self, instance):
        """Intentar reconectar con la API"""
        self.update_status("Reconnectando...")
        
        def reconnect_thread():
            self.api_connected = self.check_api_connection()
            self.update_api_status()
            self.reset_status()
        
        thread = threading.Thread(target=reconnect_thread)
        thread.daemon = True
        thread.start()
    
    def show_message(self, title, message):
        """Mostrar mensaje popup"""
        content = BackgroundLayout(orientation='vertical', padding=10)
        
        content.add_widget(Label(
            text=message,
            color=get_color_from_hex(COLORS['light_text']),
            text_size=(400, None),
            halign='center',
            font_size='11sp'
        ))
        
        close_btn = Button(
            text="Cerrar",
            size_hint=(1, 0.3),
            background_color=get_color_from_hex(COLORS['button'])
        )
        content.add_widget(close_btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.6)
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def quit_app(self, instance):
        """Cerrar aplicación"""
        print("Cerrando lector QR...")
        App.get_running_app().stop()
        sys.exit(0)

class QRReaderApp(App):
    def build(self):
        Window.clearcolor = get_color_from_hex(COLORS['dark_bg'])
        return QRReaderSimple()

if __name__ == '__main__':
    try:
        print("=== LECTOR QR SIMPLE - LABORATORIO INFORMÁTICA ===")
        print("Funcionalidades:")
        print("- Procesamiento manual de códigos QR")
        print("- Conexión con API remota")
        print("- Registro de asistencia automático")
        print("- Interfaz gráfica simplificada")
        print("=" * 55)
        
        QRReaderApp().run()
    except Exception as e:
        print(f"Error crítico en la aplicación: {e}")
        sys.exit(1)