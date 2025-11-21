# -*- coding: utf-8 -*-
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.utils import get_color_from_hex
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.popup import Popup

import cv2
import numpy as np
import time
import json
from datetime import datetime
import threading
import sys
import pymysql
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar ventana
Window.size = (800, 600)
Window.resizable = False

# Configuración de base de datos
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DB', 'horarios_lab'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Colores para la interfaz moderna
COLORS = {
    'primary': '#667eea',           # Azul moderno
    'primary_dark': '#5a67d8',     # Azul más oscuro
    'success': '#48bb78',          # Verde suave
    'success_light': '#68d391',    # Verde claro
    'error': '#f56565',            # Rojo suave
    'error_light': '#fc8181',      # Rojo claro
    'warning': '#ed8936',          # Naranja suave
    'warning_light': '#f6ad55',    # Naranja claro
    'dark_bg': '#1a202c',          # Fondo oscuro moderno
    'card_bg': '#2d3748',          # Fondo de tarjetas
    'light_text': '#f7fafc',       # Texto claro
    'secondary_text': '#a0aec0',   # Texto secundario
    'accent': '#805ad5',           # Púrpura moderno
    'accent_light': '#9f7aea',     # Púrpura claro
    'button': '#4299e1',           # Botón azul
    'button_hover': '#3182ce',     # Botón hover
    'entry': '#38a169',            # Verde entrada
    'exit': '#dd6b20',             # Naranja salida
    'qr_frame': '#fbd38d',         # Marco QR dorado
    'shadow': '#00000040'          # Sombra
}

class ModernCard(BoxLayout):
    """Tarjeta moderna con bordes redondeados y sombra"""
    def __init__(self, bg_color=COLORS['card_bg'], border_radius=15, padding_val=20, **kwargs):
        super(ModernCard, self).__init__(**kwargs)
        self.padding = [padding_val] * 4
        self.bg_color = get_color_from_hex(bg_color)
        self.border_radius = border_radius
        
        with self.canvas.before:
            Color(*self.bg_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self._update_graphics, size=self._update_graphics)
    
    def _update_graphics(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Sombra sutil
            Color(*get_color_from_hex(COLORS['shadow']))
            Rectangle(pos=(self.pos[0] + 3, self.pos[1] - 3), size=self.size)
            
            # Fondo principal
            Color(*self.bg_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

class GradientBackground(BoxLayout):
    """Fondo con gradiente"""
    def __init__(self, color1=COLORS['dark_bg'], color2=COLORS['card_bg'], **kwargs):
        super(GradientBackground, self).__init__(**kwargs)
        self.color1 = get_color_from_hex(color1)
        self.color2 = get_color_from_hex(color2)
        
        with self.canvas.before:
            Color(*self.color1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self._update_rect, size=self._update_rect)
    
    def _update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

class StatusIndicator(Label):
    """Indicador de estado con colores dinámicos"""
    def __init__(self, status_type='info', **kwargs):
        super(StatusIndicator, self).__init__(**kwargs)
        self.status_type = status_type
        self.font_size = '12sp'
        self.bold = True
        self.update_appearance()
    
    def update_appearance(self):
        status_colors = {
            'success': COLORS['success'],
            'error': COLORS['error'],
            'warning': COLORS['warning'],
            'info': COLORS['button'],
            'active': COLORS['entry']
        }
        self.color = get_color_from_hex(status_colors.get(self.status_type, COLORS['secondary_text']))

class DatabaseManager:
    """Manejador de base de datos MySQL"""
    
    @staticmethod
    def get_connection():
        """Obtiene una conexión a la base de datos"""
        try:
            connection = pymysql.connect(**DB_CONFIG)
            return connection
        except Exception as e:
            print(f"Error conectando a MySQL: {e}")
            return None
    
    @staticmethod
    def test_connection():
        """Prueba la conexión a la base de datos"""
        connection = DatabaseManager.get_connection()
        if connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    connection.close()
                return True
            except Exception as e:
                print(f"Error probando conexión: {e}")
                return False
        return False
    
    @staticmethod
    def process_qr_data(qr_data):
        """Procesar datos del QR y registrar en base de datos"""
        connection = DatabaseManager.get_connection()
        if not connection:
            return {"success": False, "message": "Error de conexión a base de datos"}
        
        try:
            # Parsear datos del QR
            if isinstance(qr_data, str):
                try:
                    qr_json = json.loads(qr_data)
                except json.JSONDecodeError:
                    return {"success": False, "message": "Formato QR inválido"}
            else:
                qr_json = qr_data
            
            # Extraer datos del QR
            name = qr_json.get('name', qr_json.get('nombre', ''))
            surname = qr_json.get('surname', qr_json.get('apellido', ''))
            email = qr_json.get('email', '')
            user_type = qr_json.get('type', qr_json.get('tipo', ''))
            
            if not all([name, surname, email]):
                return {"success": False, "message": "Datos QR incompletos"}
            
            with connection.cursor() as cursor:
                # Buscar primero en usuarios_permitidos (ayudantes)
                cursor.execute("""
                    SELECT id, nombre, apellido, email, TP as tipo, activo 
                    FROM usuarios_permitidos 
                    WHERE email = %s AND activo = 1
                """, (email,))
                
                user = cursor.fetchone()
                
                # Si no se encuentra, buscar en usuarios_estudiantes
                if not user:
                    cursor.execute("""
                        SELECT id, nombre, apellido, email, TP as tipo, activo 
                        FROM usuarios_estudiantes 
                        WHERE email = %s AND activo = 1
                    """, (email,))
                    
                    user = cursor.fetchone()
                
                if not user:
                    return {"success": False, "message": f"Usuario no autorizado: {email}"}
                
                # Determinar tipo de registro (Entrada/Salida)
                now = datetime.now()
                fecha_hoy = now.strftime("%Y-%m-%d")
                
                cursor.execute("""
                    SELECT COUNT(*) as registros
                    FROM registros 
                    WHERE email = %s AND fecha = %s
                """, (email, fecha_hoy))
                
                result = cursor.fetchone()
                count = result['registros'] if result else 0
                tipo_registro = "Entrada" if count % 2 == 0 else "Salida"
                
                # Insertar registro
                hora_actual = now.strftime("%H:%M:%S")
                dia_semana = now.strftime("%A")
                
                cursor.execute("""
                    INSERT INTO registros (fecha, hora, dia, nombre, apellido, email, metodo, tipo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (fecha_hoy, hora_actual, dia_semana, name, surname, email, 'QR', tipo_registro))
                
                connection.commit()
                
                return {
                    "success": True,
                    "message": f"{name} {surname}",
                    "tipo": tipo_registro,
                    "usuario_tipo": user['tipo'],
                    "fecha": fecha_hoy,
                    "hora": hora_actual
                }
                
        except Exception as e:
            print(f"Error procesando QR: {e}")
            connection.rollback()
            return {"success": False, "message": f"Error interno: {str(e)[:50]}"}
        finally:
            connection.close()

class QRReaderSystem(GradientBackground):
    def __init__(self, **kwargs):
        super(QRReaderSystem, self).__init__(**kwargs)
        self.orientation = 'vertical'
        
        # Configuración de cámara
        self.capture = None
        self.camera_active = False
        self.init_camera()
        
        # Estado del sistema
        self.is_scanning = True
        self.last_scan_time = 0
        self.scan_cooldown = 2.0
        self.db_busy = False
        
        # Estado de acceso
        self.access_status = None
        self.access_display_start = 0
        self.access_display_duration = 3
        
        # Verificar conexión a base de datos
        self.db_connected = DatabaseManager.test_connection()
        
        # Configurar interfaz
        self.setup_ui()
        
        # Iniciar loop de cámara si está disponible
        if self.camera_active:
            Clock.schedule_interval(self.update_camera, 1.0 / 5.0)  # 5 FPS para mejor detección
        
        print("Lector QR con MySQL iniciado")
        print(f"Base de datos: {'CONECTADA' if self.db_connected else 'ERROR'}")
    
    def init_camera(self):
        """Inicializar cámara de forma segura"""
        try:
            for camera_index in range(3):
                self.capture = cv2.VideoCapture(camera_index)
                if self.capture.isOpened():
                    self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.capture.set(cv2.CAP_PROP_FPS, 10)
                    
                    ret, frame = self.capture.read()
                    if ret and frame is not None:
                        self.camera_active = True
                        print(f"Cámara inicializada correctamente en índice {camera_index}")
                        return
                    else:
                        self.capture.release()
                        self.capture = None
            
            print("No se pudo encontrar una cámara funcional")
            self.camera_active = False
            
        except Exception as e:
            print(f"Error al inicializar cámara: {e}")
            self.camera_active = False
            self.capture = None
    
    def setup_ui(self):
        """Configurar interfaz de usuario moderna"""
        self.padding = [20, 20, 20, 20]
        self.spacing = 15
        
        # Header moderno con degradado
        header = ModernCard(
            orientation='vertical', 
            size_hint=(1, 0.15), 
            bg_color=COLORS['primary'],
            padding_val=25
        )
        
        # Título principal con estilo
        self.title_label = Label(
            text="🔍 LECTOR QR LABORATORIO",
            font_size='24sp',
            bold=True,
            color=get_color_from_hex(COLORS['light_text']),
            size_hint=(1, 0.6)
        )
        header.add_widget(self.title_label)
        
        # Subtítulo elegante
        subtitle = Label(
            text="Universidad Adolfo Ibáñez • Informática • MySQL Direct",
            font_size='13sp',
            color=get_color_from_hex(COLORS['secondary_text']),
            size_hint=(1, 0.4)
        )
        header.add_widget(subtitle)
        self.add_widget(header)
        
        # Layout principal con espaciado moderno
        main_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.75), spacing=20)
        
        # Panel izquierdo - Cámara con tarjeta moderna
        camera_card = ModernCard(
            orientation='vertical', 
            size_hint=(0.65, 1),
            bg_color=COLORS['card_bg'],
            padding_val=15
        )
        
        # Título de sección de cámara
        camera_title = Label(
            text="📷 Vista de Cámara",
            font_size='16sp',
            bold=True,
            color=get_color_from_hex(COLORS['light_text']),
            size_hint=(1, 0.08)
        )
        camera_card.add_widget(camera_title)
        
        # Vista de cámara con marco elegante
        if self.camera_active:
            camera_container = ModernCard(
                size_hint=(1, 0.82),
                bg_color=COLORS['dark_bg'],
                padding_val=5
            )
            self.camera_image = Image(size_hint=(1, 1))
            camera_container.add_widget(self.camera_image)
            camera_card.add_widget(camera_container)
        else:
            camera_error_card = ModernCard(
                size_hint=(1, 0.82),
                bg_color=COLORS['error'],
                padding_val=30
            )
            camera_error = Label(
                text="📹 CÁMARA NO DISPONIBLE\n\n🔌 Conecte una cámara web\n⚠️ Cierre otras aplicaciones\n🔄 Presione 'Reintentar'",
                font_size='14sp',
                color=get_color_from_hex(COLORS['light_text']),
                size_hint=(1, 1),
                text_size=(None, None),
                halign='center',
                valign='center'
            )
            camera_error_card.add_widget(camera_error)
            camera_card.add_widget(camera_error_card)
        
        # Botones de cámara con estilo moderno
        camera_buttons = BoxLayout(
            orientation='horizontal', 
            size_hint=(1, 0.1), 
            spacing=10
        )
        
        self.scan_button = Button(
            text="⏸️ PAUSAR" if self.camera_active else "❌ CÁMARA NO DISPONIBLE",
            background_color=get_color_from_hex(COLORS['warning'] if self.camera_active else COLORS['error']),
            color=get_color_from_hex(COLORS['light_text']),
            bold=True,
            disabled=not self.camera_active,
            font_size='12sp'
        )
        if self.camera_active:
            self.scan_button.bind(on_press=self.toggle_scanning)
        
        retry_camera_button = Button(
            text="🔄 REINTENTAR",
            background_color=get_color_from_hex(COLORS['accent']),
            color=get_color_from_hex(COLORS['light_text']),
            bold=True,
            font_size='12sp'
        )
        retry_camera_button.bind(on_press=self.retry_camera)
        
        camera_buttons.add_widget(self.scan_button)
        camera_buttons.add_widget(retry_camera_button)
        camera_card.add_widget(camera_buttons)
        
        main_layout.add_widget(camera_card)
        
        # Panel derecho - Dashboard moderno
        right_panel = BoxLayout(
            orientation='vertical',
            size_hint=(0.35, 1),
            spacing=15
        )
        
        # Tarjeta de estado principal
        status_card = ModernCard(
            orientation='vertical',
            size_hint=(1, 0.25),
            bg_color=COLORS['success'] if (self.camera_active and self.db_connected) else COLORS['error'],
            padding_val=20
        )
        
        # Icono y estado principal
        status_icon = "✅" if (self.camera_active and self.db_connected) else "⚠️"
        if self.camera_active and self.db_connected:
            status_text = f"{status_icon} SISTEMA OPERATIVO"
            status_subtitle = "Listo para escanear códigos QR"
        elif not self.camera_active:
            status_text = f"{status_icon} CÁMARA ERROR"
            status_subtitle = "Conecte una cámara web"
        elif not self.db_connected:
            status_text = f"{status_icon} BASE DATOS ERROR"
            status_subtitle = "Verifique conexión MySQL"
        else:
            status_text = f"{status_icon} SISTEMA INACTIVO"
            status_subtitle = "Múltiples errores detectados"
            
        self.status_label = Label(
            text=status_text,
            font_size='16sp',
            bold=True,
            color=get_color_from_hex(COLORS['light_text']),
            size_hint=(1, 0.6)
        )
        status_card.add_widget(self.status_label)
        
        status_subtitle_label = Label(
            text=status_subtitle,
            font_size='11sp',
            color=get_color_from_hex(COLORS['light_text']),
            size_hint=(1, 0.4),
            opacity=0.8
        )
        status_card.add_widget(status_subtitle_label)
        right_panel.add_widget(status_card)
        
        # Tarjeta de información detallada
        info_card = ModernCard(
            orientation='vertical',
            size_hint=(1, 0.35),
            bg_color=COLORS['card_bg'],
            padding_val=20
        )
        
        info_title = Label(
            text="📋 Información del Sistema",
            font_size='14sp',
            bold=True,
            color=get_color_from_hex(COLORS['light_text']),
            size_hint=(1, 0.2)
        )
        info_card.add_widget(info_title)
        
        if self.camera_active and self.db_connected:
            info_text = "🔍 Sistema listo para operar\n\n📷 Apunte códigos QR al centro\n🔒 Conexión MySQL segura\n⚡ Detección automática activa"
        elif not self.camera_active:
            info_text = "⚠️ Cámara no disponible\n\n🔌 Conecte una cámara web\n❌ Cierre otras aplicaciones\n🔄 Use el botón 'Reintentar'"
        elif not self.db_connected:
            info_text = "⚠️ Error de base de datos\n\n🔧 Verifique archivo .env\n🌐 Confirme conectividad\n📞 Contacte soporte técnico"
        else:
            info_text = "❌ Sistema no operativo\n\n🔧 Múltiples componentes fallan\n⚠️ Revise cámara y MySQL\n🆘 Reinicie la aplicación"
            
        self.info_label = Label(
            text=info_text,
            font_size='11sp',
            color=get_color_from_hex(COLORS['secondary_text']),
            size_hint=(1, 0.8),
            text_size=(None, None),
            halign='left',
            valign='top'
        )
        info_card.add_widget(self.info_label)
        right_panel.add_widget(info_card)
        
        # Tarjeta de estado de componentes
        status_components_card = ModernCard(
            orientation='vertical',
            size_hint=(1, 0.25),
            bg_color=COLORS['card_bg'],
            padding_val=15
        )
        
        components_title = Label(
            text="🔧 Estado de Componentes",
            font_size='13sp',
            bold=True,
            color=get_color_from_hex(COLORS['light_text']),
            size_hint=(1, 0.3)
        )
        status_components_card.add_widget(components_title)
        
        # Estados con iconos
        db_icon = "🟢" if self.db_connected else "🔴"
        camera_icon = "🟢" if self.camera_active else "🔴"
        
        self.db_status_label = Label(
            text=f"{db_icon} MySQL: {'CONECTADA' if self.db_connected else 'ERROR'}",
            font_size='11sp',
            color=get_color_from_hex(COLORS['success'] if self.db_connected else COLORS['error']),
            size_hint=(1, 0.35)
        )
        status_components_card.add_widget(self.db_status_label)
        
        self.camera_status_label = Label(
            text=f"{camera_icon} Cámara: {'OPERATIVA' if self.camera_active else 'ERROR'}",
            font_size='11sp',
            color=get_color_from_hex(COLORS['success'] if self.camera_active else COLORS['error']),
            size_hint=(1, 0.35)
        )
        status_components_card.add_widget(self.camera_status_label)
        right_panel.add_widget(status_components_card)
        
        # Botones de acción modernos
        actions_card = ModernCard(
            orientation='vertical',
            size_hint=(1, 0.15),
            bg_color=COLORS['card_bg'],
            padding_val=10
        )
        
        # Botón de reconectar DB
        reconnect_db_button = Button(
            text="🔄 RECONECTAR MySQL",
            background_color=get_color_from_hex(COLORS['accent']),
            color=get_color_from_hex(COLORS['light_text']),
            bold=True,
            size_hint=(1, 0.45),
            font_size='11sp'
        )
        reconnect_db_button.bind(on_press=self.reconnect_db)
        actions_card.add_widget(reconnect_db_button)
        
        # Botón de salir
        quit_button = Button(
            text="❌ SALIR",
            background_color=get_color_from_hex(COLORS['error']),
            color=get_color_from_hex(COLORS['light_text']),
            bold=True,
            size_hint=(1, 0.45),
            font_size='11sp'
        )
        quit_button.bind(on_press=self.quit_app)
        actions_card.add_widget(quit_button)
        right_panel.add_widget(actions_card)
        
        main_layout.add_widget(right_panel)
        self.add_widget(main_layout)
    
    def retry_camera(self, instance):
        """Reintentar inicializar cámara"""
        print("Reintentando conexión de cámara...")
        if self.capture:
            self.capture.release()
        
        self.init_camera()
        
        if self.camera_active:
            self.camera_status_label.text = "CÁMARA: OK"
            self.camera_status_label.color = get_color_from_hex(COLORS['success'])
            self.scan_button.disabled = False
            self.scan_button.text = "PAUSAR"
            self.scan_button.background_color = get_color_from_hex(COLORS['button'])
            
            if not hasattr(self, 'camera_image'):
                self.clear_widgets()
                self.setup_ui()
            
            Clock.unschedule(self.update_camera)
            Clock.schedule_interval(self.update_camera, 1.0 / 5.0)
        else:
            self.camera_status_label.text = "CÁMARA: ERROR"
            self.camera_status_label.color = get_color_from_hex(COLORS['error'])
        
        self.update_system_status()
    
    def reconnect_db(self, instance):
        """Intentar reconectar a la base de datos"""
        def reconnect_thread():
            self.db_connected = DatabaseManager.test_connection()
            Clock.schedule_once(lambda dt: self.update_db_status(), 0)
            Clock.schedule_once(lambda dt: self.update_system_status(), 0)
        
        thread = threading.Thread(target=reconnect_thread)
        thread.daemon = True
        thread.start()
    
    def update_camera(self, dt):
        """Actualizar frame de cámara y procesar QR"""
        if not self.camera_active or not self.capture:
            return
        
        ret, frame = self.capture.read()
        
        if ret and frame is not None:
            frame = cv2.flip(frame, 1)
            display_frame = frame.copy()
            
            current_time = time.time()
            
            if self.access_status is not None and current_time - self.access_display_start < self.access_display_duration:
                self.draw_access_result(display_frame, current_time)
            elif current_time - self.access_display_start >= self.access_display_duration:
                self.access_status = None
            
            if self.is_scanning and not self.db_busy and self.db_connected:
                self.process_qr_detection(frame, display_frame, current_time)
            
            self.update_camera_display(display_frame)
        else:
            print("Error leyendo frame de cámara")
            self.camera_active = False
            self.retry_camera(None)
    
    def process_qr_detection(self, frame, display_frame, current_time):
        """Procesar detección de QR"""
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Probar múltiples métodos de detección
            qr_codes = []
            
            # Método 1: Imagen original
            qr_codes = pyzbar.decode(gray, symbols=[ZBarSymbol.QRCODE])
            
            # Método 2: Si no encuentra nada, probar con ecualización
            if not qr_codes:
                equalized = cv2.equalizeHist(gray)
                qr_codes = pyzbar.decode(equalized, symbols=[ZBarSymbol.QRCODE])
            
            # Método 3: Si aún no encuentra, probar con umbralización adaptativa
            if not qr_codes:
                adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
                qr_codes = pyzbar.decode(adaptive, symbols=[ZBarSymbol.QRCODE])
            
            # Mostrar área de detección elegante
            height, width = display_frame.shape[:2]
            center_x, center_y = width // 2, height // 2
            box_size = min(width, height) // 4
            
            # Crear marco de detección con esquinas redondeadas
            corner_length = 30
            thickness = 3
            
            # Color dorado para el marco (RGB en BGR)
            frame_color = (89, 193, 251)  # Dorado en BGR
            
            # Esquinas superiores
            cv2.line(display_frame, 
                    (center_x - box_size, center_y - box_size), 
                    (center_x - box_size + corner_length, center_y - box_size), 
                    frame_color, thickness)
            cv2.line(display_frame, 
                    (center_x - box_size, center_y - box_size), 
                    (center_x - box_size, center_y - box_size + corner_length), 
                    frame_color, thickness)
            
            cv2.line(display_frame, 
                    (center_x + box_size, center_y - box_size), 
                    (center_x + box_size - corner_length, center_y - box_size), 
                    frame_color, thickness)
            cv2.line(display_frame, 
                    (center_x + box_size, center_y - box_size), 
                    (center_x + box_size, center_y - box_size + corner_length), 
                    frame_color, thickness)
            
            # Esquinas inferiores
            cv2.line(display_frame, 
                    (center_x - box_size, center_y + box_size), 
                    (center_x - box_size + corner_length, center_y + box_size), 
                    frame_color, thickness)
            cv2.line(display_frame, 
                    (center_x - box_size, center_y + box_size), 
                    (center_x - box_size, center_y + box_size - corner_length), 
                    frame_color, thickness)
            
            cv2.line(display_frame, 
                    (center_x + box_size, center_y + box_size), 
                    (center_x + box_size - corner_length, center_y + box_size), 
                    frame_color, thickness)
            cv2.line(display_frame, 
                    (center_x + box_size, center_y + box_size), 
                    (center_x + box_size, center_y + box_size - corner_length), 
                    frame_color, thickness)
            
            # Texto con fondo elegante
            text = "📱 Coloque el QR aquí"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            text_thickness = 2
            
            (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, text_thickness)
            text_x = center_x - text_width // 2
            text_y = center_y + box_size + 40
            
            # Fondo del texto
            cv2.rectangle(display_frame, 
                         (text_x - 10, text_y - text_height - 5),
                         (text_x + text_width + 10, text_y + baseline + 5),
                         (0, 0, 0), -1)
            
            cv2.putText(display_frame, text, 
                       (text_x, text_y),
                       font, font_scale, frame_color, text_thickness)
            
            for qr in qr_codes:
                points = qr.polygon
                if points:
                    pts = []
                    for point in points:
                        pts.append([point.x, point.y])
                    
                    pts = np.array(pts, np.int32)
                    pts = pts.reshape((-1, 1, 2))
                    
                    # Contorno verde brillante del QR detectado
                    cv2.polylines(display_frame, [pts], True, (0, 255, 0), 4)
                    
                    # Crear overlay para efecto de brillo
                    overlay = display_frame.copy()
                    cv2.fillPoly(overlay, [pts], (0, 255, 0))
                    cv2.addWeighted(display_frame, 0.9, overlay, 0.1, 0, display_frame)
                    
                    # Texto elegante "QR DETECTADO"
                    success_text = "✅ QR DETECTADO"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.8
                    text_thickness = 2
                    
                    (text_width, text_height), baseline = cv2.getTextSize(success_text, font, font_scale, text_thickness)
                    text_x = qr.rect.left
                    text_y = qr.rect.top - 15
                    
                    # Asegurar que el texto esté dentro de la pantalla
                    if text_y < text_height:
                        text_y = qr.rect.top + qr.rect.height + text_height + 15
                    
                    # Fondo del texto con bordes redondeados (simulado)
                    cv2.rectangle(display_frame, 
                                 (text_x - 5, text_y - text_height - 5),
                                 (text_x + text_width + 5, text_y + baseline + 5),
                                 (0, 0, 0), -1)
                    
                    cv2.putText(display_frame, success_text, 
                               (text_x, text_y),
                               font, font_scale, (0, 255, 0), text_thickness)
                
                if current_time - self.last_scan_time > self.scan_cooldown:
                    qr_data = qr.data.decode('utf-8')
                    print(f"QR detectado - Tipo: {qr.type}, Datos: {qr_data[:100]}...")
                    self.process_qr_async(qr_data, current_time)
                    self.last_scan_time = current_time
            
            # Estado de búsqueda elegante
            if not qr_codes:
                status_text = "🔍 Buscando códigos QR..."
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                text_thickness = 2
                
                (text_width, text_height), baseline = cv2.getTextSize(status_text, font, font_scale, text_thickness)
                
                # Posición en la esquina superior izquierda
                cv2.rectangle(display_frame, 
                             (5, 5),
                             (text_width + 15, text_height + 15),
                             (0, 0, 0), -1)
                
                cv2.putText(display_frame, status_text, 
                           (10, text_height + 10), font, font_scale, (89, 193, 251), text_thickness)
        except Exception as e:
            print(f"Error en detección QR: {e}")
    
    def process_qr_async(self, qr_data, scan_time):
        """Procesar QR en hilo separado"""
        if self.db_busy:
            return
        
        def process_thread():
            self.db_busy = True
            try:
                self.process_qr(qr_data, scan_time)
            finally:
                self.db_busy = False
        
        thread = threading.Thread(target=process_thread)
        thread.daemon = True
        thread.start()
    
    def process_qr(self, qr_data, scan_time):
        """Procesar QR con base de datos MySQL"""
        try:
            print(f"QR detectado: {qr_data[:50]}...")
            
            Clock.schedule_once(lambda dt: self.update_status("Procesando QR..."), 0)
            
            if not self.db_connected:
                Clock.schedule_once(
                    lambda dt: self.show_access_result({
                        "success": False,
                        "message": "Sin conexión MySQL"
                    }, scan_time), 0
                )
                return
            
            # Procesar QR con base de datos
            result = DatabaseManager.process_qr_data(qr_data)
            
            Clock.schedule_once(
                lambda dt: self.show_access_result(result, scan_time), 0
            )
            
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self.show_access_result({
                    "success": False,
                    "message": f"Error: {str(e)[:30]}"
                }, scan_time), 0
            )
    
    def draw_access_result(self, display_frame, current_time):
        """Dibujar resultado de acceso en el frame"""
        overlay = display_frame.copy()
        
        if self.access_status["success"]:
            text = f"✓ {self.access_status['message']} - {self.access_status.get('tipo', '')}"
            color = (0, 255, 0)
        else:
            text = f"✗ ERROR: {self.access_status['message']}"
            color = (0, 0, 255)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8
        thickness = 2
        
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        
        x = (display_frame.shape[1] - text_width) // 2
        y = 60
        
        cv2.rectangle(overlay, (x-10, y-text_height-10), (x+text_width+10, y+baseline+10), (0, 0, 0), -1)
        cv2.putText(overlay, text, (x, y), font, font_scale, color, thickness)
        
        alpha = 0.8
        cv2.addWeighted(overlay, alpha, display_frame, 1 - alpha, 0, display_frame)
    
    def update_camera_display(self, frame):
        """Actualizar display de la cámara"""
        try:
            buf = cv2.flip(frame, 0).tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.camera_image.texture = texture
        except Exception as e:
            print(f"Error actualizando display: {e}")
    
    def show_access_result(self, result, scan_time):
        """Mostrar resultado de acceso en la UI"""
        self.access_status = result
        self.access_display_start = scan_time
        
        if result["success"]:
            status_text = f"✓ {result.get('tipo', 'Registro')} Registrado"
            color = COLORS['entry'] if result.get('tipo') == 'Entrada' else COLORS['exit']
            
            self.status_label.text = status_text
            self.status_label.color = get_color_from_hex(color)
            
            user_type = result.get('usuario_tipo', '')
            info_text = f"✓ {result['message']}\n\nTipo: {result.get('tipo', '')}\nUsuario: {user_type}\nMétodo: QR MySQL\n\nEscanee otro código QR"
            self.info_label.text = info_text
            
            print(f"ACCESO REGISTRADO: {status_text} - {result['message']}")
        else:
            self.status_label.text = "✗ ERROR"
            self.status_label.color = get_color_from_hex(COLORS['error'])
            self.info_label.text = f"✗ {result['message']}\n\nIntente nuevamente\no contacte soporte\n\nVerifique conexión MySQL\ny datos del QR"
            
            print(f"ERROR DE REGISTRO: {result['message']}")
        
        Clock.schedule_once(self.reset_status, self.access_display_duration)
    
    def reset_status(self, dt):
        """Restaurar estado inicial de la UI"""
        self.update_system_status()
    
    def update_system_status(self):
        """Actualizar estado del sistema"""
        if self.camera_active and self.db_connected:
            self.status_label.text = "Lector QR Activo" if self.is_scanning else "Pausado"
            self.status_label.color = get_color_from_hex(COLORS['success'])
            self.info_label.text = "Listo para escanear códigos QR\n\nApunte la cámara hacia un\ncódigo QR válido\n\nEl sistema registrará\nautomáticamente en MySQL"
        elif not self.camera_active:
            self.status_label.text = "Cámara No Disponible"
            self.status_label.color = get_color_from_hex(COLORS['error'])
            self.info_label.text = "La cámara no está disponible\n\nVerifique que esté conectada\ny no esté siendo usada por\notra aplicación"
        elif not self.db_connected:
            self.status_label.text = "Base de Datos Error"
            self.status_label.color = get_color_from_hex(COLORS['error'])
            self.info_label.text = "Error de conexión MySQL\n\nVerifique las credenciales\nen el archivo .env.example"
    
    def update_status(self, status_text):
        """Actualizar estado en UI"""
        self.status_label.text = status_text
        self.status_label.color = get_color_from_hex(COLORS['warning'])
    
    def update_db_status(self):
        """Actualizar estado de conexión a base de datos"""
        db_status_text = "MySQL: " + ("CONECTADA" if self.db_connected else "ERROR")
        db_color = COLORS['success'] if self.db_connected else COLORS['error']
        self.db_status_label.text = db_status_text
        self.db_status_label.color = get_color_from_hex(db_color)
    
    def toggle_scanning(self, instance):
        """Alternar escaneo/pausa"""
        self.is_scanning = not self.is_scanning
        
        if self.is_scanning:
            self.scan_button.text = "PAUSAR"
            self.scan_button.background_color = get_color_from_hex(COLORS['button'])
        else:
            self.scan_button.text = "REANUDAR"
            self.scan_button.background_color = get_color_from_hex(COLORS['accent'])
        
        self.update_system_status()
    
    def quit_app(self, instance):
        """Cerrar aplicación"""
        print("Cerrando lector QR...")
        if self.capture:
            self.capture.release()
        
        Clock.unschedule(self.update_camera)
        App.get_running_app().stop()
        sys.exit(0)

class QRReaderApp(App):
    def build(self):
        Window.clearcolor = get_color_from_hex(COLORS['dark_bg'])
        return QRReaderSystem()

if __name__ == '__main__':
    try:
        print("=== LECTOR QR - LABORATORIO INFORMÁTICA (MySQL Direct) ===")
        print("Funcionalidades:")
        print("- Lectura automática de códigos QR con cámara")
        print("- Conexión directa con base de datos MySQL")
        print("- Registro de asistencia automático")
        print("- Sin dependencia de API externa")
        print("=" * 60)
        
        QRReaderApp().run()
    except Exception as e:
        print(f"Error crítico en la aplicación: {e}")
        sys.exit(1)