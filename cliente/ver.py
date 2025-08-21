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
    'exit': '#e67e22',
    'qr_mode': '#16a085'
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

class QRReaderSystem(BackgroundLayout):
    def __init__(self, **kwargs):
        super(QRReaderSystem, self).__init__(bg_color=COLORS['dark_bg'], **kwargs)
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
            Clock.schedule_interval(self.update_camera, 1.0 / 10.0)
        
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
        """Configurar interfaz de usuario"""
        # Header con título
        header = BackgroundLayout(
            orientation='horizontal', 
            size_hint=(1, 0.1), 
            bg_color=COLORS['dark_bg']
        )
        
        self.title_label = Label(
            text="LECTOR QR - LABORATORIO INFORMÁTICA (MySQL Direct)",
            font_size='16sp',
            bold=True,
            color=get_color_from_hex(COLORS['light_text'])
        )
        header.add_widget(self.title_label)
        self.add_widget(header)
        
        # Layout principal
        main_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.8))
        
        # Panel izquierdo - Cámara
        left_panel = BackgroundLayout(
            orientation='vertical', 
            size_hint=(0.7, 1), 
            bg_color=COLORS['dark_bg']
        )
        
        # Vista de cámara
        if self.camera_active:
            self.camera_image = Image(size_hint=(1, 0.9))
            left_panel.add_widget(self.camera_image)
        else:
            camera_error = Label(
                text="CÁMARA NO DISPONIBLE\n\nNo se pudo acceder a la cámara.\nVerifique que esté conectada\ny no esté siendo usada por\notra aplicación.",
                font_size='14sp',
                color=get_color_from_hex(COLORS['error']),
                size_hint=(1, 0.9),
                text_size=(None, None),
                halign='center',
                valign='center'
            )
            left_panel.add_widget(camera_error)
        
        # Botones de cámara
        camera_buttons = BoxLayout(
            orientation='horizontal', 
            size_hint=(1, 0.1), 
            spacing=5
        )
        
        self.scan_button = Button(
            text="PAUSAR" if self.camera_active else "CÁMARA NO DISPONIBLE",
            background_color=get_color_from_hex(COLORS['button'] if self.camera_active else COLORS['error']),
            color=get_color_from_hex(COLORS['light_text']),
            bold=True,
            disabled=not self.camera_active
        )
        if self.camera_active:
            self.scan_button.bind(on_press=self.toggle_scanning)
        
        retry_camera_button = Button(
            text="REINTENTAR CÁMARA",
            background_color=get_color_from_hex(COLORS['accent']),
            color=get_color_from_hex(COLORS['light_text']),
            bold=True
        )
        retry_camera_button.bind(on_press=self.retry_camera)
        
        camera_buttons.add_widget(self.scan_button)
        camera_buttons.add_widget(retry_camera_button)
        left_panel.add_widget(camera_buttons)
        
        main_layout.add_widget(left_panel)
        
        # Panel derecho - Información
        right_panel = BackgroundLayout(
            orientation='vertical', 
            size_hint=(0.3, 1),
            bg_color=COLORS['dark_bg'], 
            padding=[10, 5], 
            spacing=5
        )
        
        # Estado del sistema
        if self.camera_active and self.db_connected:
            status_text = "Lector QR Activo"
            status_color = COLORS['success']
        elif not self.camera_active:
            status_text = "Cámara No Disponible"
            status_color = COLORS['error']
        elif not self.db_connected:
            status_text = "Base de Datos Error"
            status_color = COLORS['error']
        else:
            status_text = "Sistema No Operativo"
            status_color = COLORS['error']
            
        self.status_label = Label(
            text=status_text,
            font_size='14sp',
            bold=True,
            color=get_color_from_hex(status_color),
            size_hint=(1, 0.15),
            text_size=(None, None),
            halign='center'
        )
        right_panel.add_widget(self.status_label)
        
        # Información detallada
        if self.camera_active and self.db_connected:
            info_text = "Listo para escanear códigos QR\n\nApunte la cámara hacia un\ncódigo QR válido\n\nEl sistema registrará\nautomáticamente en MySQL"
        elif not self.camera_active:
            info_text = "La cámara no está disponible\n\nVerifique que esté conectada\ny no esté siendo usada por\notra aplicación"
        elif not self.db_connected:
            info_text = "Error de conexión MySQL\n\nVerifique las credenciales\nen el archivo .env.example\n\nHost, usuario, contraseña\ny base de datos"
        else:
            info_text = "Sistema no operativo\n\nRevise la cámara y\nla conexión MySQL"
            
        self.info_label = Label(
            text=info_text,
            font_size='10sp',
            color=get_color_from_hex(COLORS['light_text']),
            size_hint=(1, 0.4),
            text_size=(None, None),
            halign='left',
            valign='top'
        )
        right_panel.add_widget(self.info_label)
        
        # Estado de base de datos
        db_status_text = "MySQL: " + ("CONECTADA" if self.db_connected else "ERROR")
        db_color = COLORS['success'] if self.db_connected else COLORS['error']
        
        self.db_status_label = Label(
            text=db_status_text,
            font_size='11sp',
            bold=True,
            color=get_color_from_hex(db_color),
            size_hint=(1, 0.1)
        )
        right_panel.add_widget(self.db_status_label)
        
        # Estado de cámara
        camera_status_text = "CÁMARA: " + ("OK" if self.camera_active else "ERROR")
        camera_color = COLORS['success'] if self.camera_active else COLORS['error']
        
        self.camera_status_label = Label(
            text=camera_status_text,
            font_size='11sp',
            bold=True,
            color=get_color_from_hex(camera_color),
            size_hint=(1, 0.1)
        )
        right_panel.add_widget(self.camera_status_label)
        
        # Botón de reconectar DB
        reconnect_db_button = Button(
            text="RECONECTAR MySQL",
            background_color=get_color_from_hex(COLORS['accent']),
            color=get_color_from_hex(COLORS['light_text']),
            bold=True,
            size_hint=(1, 0.1)
        )
        reconnect_db_button.bind(on_press=self.reconnect_db)
        right_panel.add_widget(reconnect_db_button)
        
        # Botón de salir
        quit_button = Button(
            text="SALIR",
            background_color=get_color_from_hex(COLORS['error']),
            color=get_color_from_hex(COLORS['light_text']),
            bold=True,
            size_hint=(1, 0.1)
        )
        quit_button.bind(on_press=self.quit_app)
        right_panel.add_widget(quit_button)
        
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
            Clock.schedule_interval(self.update_camera, 1.0 / 10.0)
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
            # Mejorar la imagen para mejor detección
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Aplicar filtros para mejorar la detección
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Decodificar solo códigos QR (evita problemas con PDF417)
            qr_codes = pyzbar.decode(gray, symbols=[ZBarSymbol.QRCODE])
            
            for qr in qr_codes:
                points = qr.polygon
                if points:
                    pts = []
                    for point in points:
                        pts.append([point.x, point.y])
                    
                    pts = np.array(pts, np.int32)
                    pts = pts.reshape((-1, 1, 2))
                    cv2.polylines(display_frame, [pts], True, (0, 255, 0), 3)
                    
                    cv2.putText(display_frame, "QR DETECTADO", 
                               (qr.rect.left, qr.rect.top - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                if current_time - self.last_scan_time > self.scan_cooldown:
                    qr_data = qr.data.decode('utf-8')
                    self.process_qr_async(qr_data, current_time)
                    self.last_scan_time = current_time
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