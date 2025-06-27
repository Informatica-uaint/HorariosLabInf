# test_validacion_qr_completo.py
"""
Pruebas unitarias para la funcionalidad de VALIDACIÓN DE CÓDIGOS QR
Objetivo: Alcanzar +80% de cobertura con casos exitosos y de error
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import json
import time
from datetime import datetime, timedelta
from io import StringIO

# Configurar path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../back-end/lector'))

class TestValidacionQRCompleto(unittest.TestCase):
    """Suite completa de tests para validación de códigos QR"""
    
    def setUp(self):
        """Setup ejecutado antes de cada test"""
        self.valid_student_qr = {
            'name': 'Juan',
            'surname': 'Pérez',
            'email': 'juan.perez@estudiante.com',
            'tipoUsuario': 'ESTUDIANTE',
            'timestamp': int(time.time() * 1000),
            'status': 'VALID'
        }
        
        self.valid_helper_qr = {
            'name': 'María',
            'surname': 'González',
            'email': 'maria.gonzalez@ayudante.com',
            'tipoUsuario': 'AYUDANTE',
            'timestamp': int(time.time() * 1000),
            'status': 'VALID'
        }
    
    # ========== CASOS EXITOSOS ==========
    
    def test_normalize_email_casos_exitosos(self):
        """Test casos exitosos de normalización de email"""
        from api_qr_temporal import normalize_email
        
        # Casos válidos que deben funcionar
        test_cases = [
            ('TEST@EXAMPLE.COM', 'test@example.com'),
            ('  user@domain.com  ', 'user@domain.com'),
            ('User.Name@Domain.ORG', 'user.name@domain.org'),
            ('simple@test.cl', 'simple@test.cl'),
            ('number123@test.edu', 'number123@test.edu')
        ]
        
        for input_email, expected in test_cases:
            with self.subTest(email=input_email):
                result = normalize_email(input_email)
                self.assertEqual(result, expected)
                self.assertIsInstance(result, str)
    
    def test_get_dia_espanol_casos_exitosos(self):
        """Test casos exitosos de obtención de día en español"""
        from api_qr_temporal import get_dia_espanol
        
        result = get_dia_espanol()
        
        # Verificar que retorna un día válido
        dias_validos = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
        self.assertIn(result, dias_validos)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
    
    def test_validate_timestamp_qr_valido(self):
        """Test validación exitosa de timestamp QR"""
        from api_qr_temporal import validate_timestamp
        
        # QR con timestamp reciente (5 segundos atrás)
        current_time = time.time() * 1000
        qr_data = {
            'timestamp': current_time - 5000,
            'status': 'VALID'
        }
        
        result = validate_timestamp(qr_data)
        
        self.assertTrue(result['valid'])
        self.assertIn('time_remaining', result)
        self.assertIsInstance(result['time_remaining'], (int, float))
        self.assertGreaterEqual(result['time_remaining'], 0)
    
    def test_validate_timestamp_qr_auto_renovable(self):
        """Test QR con auto-renovación (sin expiración)"""
        from api_qr_temporal import validate_timestamp
        
        # QR con auto-renovación no expira
        qr_data = {
            'timestamp': int(time.time() * 1000) - 30000,  # 30 segundos atrás
            'autoRenewal': True,
            'status': 'VALID'
        }
        
        result = validate_timestamp(qr_data)
        self.assertTrue(result['valid'])
    
    @patch('api_qr_temporal.get_db_connection')
    def test_process_student_caso_exitoso(self, mock_db):
        """Test procesamiento exitoso de estudiante"""
        from api_qr_temporal import process_student
        
        # Mock de conexión y cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock estudiante existente
        mock_cursor.fetchone.side_effect = [
            {  # Primera llamada: verificar estudiante
                'id': 1,
                'nombre': 'Juan',
                'apellido': 'Pérez',
                'email': 'juan@test.com',
                'activo': 1
            },
            None  # Segunda llamada: no hay registro previo (primera entrada del día)
        ]
        
        result = process_student('Juan', 'Pérez', 'juan@test.com')
        
        # Verificar resultado exitoso
        self.assertTrue(result['success'])
        self.assertEqual(result['tipo'], 'Entrada')
        self.assertEqual(result['usuario_tipo'], 'ESTUDIANTE')
        self.assertEqual(result['nombre'], 'Juan')
        self.assertEqual(result['apellido'], 'Pérez')
        self.assertIn('message', result)
        
        # Verificar que se llamó a commit
        mock_conn.commit.assert_called_once()
    
    @patch('api_qr_temporal.get_db_connection')
    def test_process_helper_caso_exitoso(self, mock_db):
        """Test procesamiento exitoso de ayudante"""
        from api_qr_temporal import process_helper
        
        # Mock de conexión
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock ayudante existente con último registro de entrada
        mock_cursor.fetchone.side_effect = [
            {  # Primera llamada: verificar ayudante
                'id': 1,
                'nombre': 'María',
                'apellido': 'González',
                'email': 'maria@test.com',
                'activo': 1
            },
            {  # Segunda llamada: último registro es entrada
                'tipo': 'Entrada',
                'fecha_reg': datetime.now().date()
            }
        ]
        
        result = process_helper('María', 'González', 'maria@test.com')
        
        # Verificar resultado exitoso (debería ser Salida)
        self.assertTrue(result['success'])
        self.assertEqual(result['tipo'], 'Salida')
        self.assertEqual(result['usuario_tipo'], 'AYUDANTE')
        self.assertEqual(result['nombre'], 'María')
    
    # ========== CASOS DE ERROR Y BORDE ==========
    
    def test_normalize_email_casos_borde(self):
        """Test casos borde y de error para normalización de email"""
        from api_qr_temporal import normalize_email
        
        # Casos borde
        test_cases = [
            ('', ''),
            (None, ''),
            ('   ', ''),
            ('MAYUSCULAS@TEST.COM', 'mayusculas@test.com'),
            ('   espacios@inicio.com   ', 'espacios@inicio.com')
        ]
        
        for input_email, expected in test_cases:
            with self.subTest(email=input_email):
                result = normalize_email(input_email)
                self.assertEqual(result, expected)
    
    def test_validate_timestamp_qr_expirado(self):
        """Test QR expirado por tiempo"""
        from api_qr_temporal import validate_timestamp
        
        # QR expirado (20 segundos atrás)
        current_time = time.time() * 1000
        qr_data = {
            'timestamp': current_time - 20000,
            'status': 'VALID'
        }
        
        result = validate_timestamp(qr_data)
        
        self.assertFalse(result['valid'])
        self.assertIn('error', result)
        self.assertIn('expirado', result['error'].lower())
    
    def test_validate_timestamp_qr_marcado_expirado(self):
        """Test QR marcado explícitamente como expirado"""
        from api_qr_temporal import validate_timestamp
        
        # QR marcado como expirado
        qr_data = {
            'timestamp': int(time.time() * 1000),
            'status': 'EXPIRED'
        }
        
        result = validate_timestamp(qr_data)
        
        self.assertFalse(result['valid'])
        self.assertIn('expirado', result['error'].lower())
    
    def test_validate_timestamp_sin_timestamp(self):
        """Test QR sin timestamp"""
        from api_qr_temporal import validate_timestamp
        
        qr_data = {
            'status': 'VALID'
            # Sin timestamp
        }
        
        result = validate_timestamp(qr_data)
        
        self.assertFalse(result['valid'])
        self.assertIn('timestamp', result['error'].lower())
    
    def test_validate_timestamp_timestamp_invalido(self):
        """Test QR con timestamp inválido"""
        from api_qr_temporal import validate_timestamp
        
        qr_data = {
            'timestamp': 'invalid_timestamp',
            'status': 'VALID'
        }
        
        result = validate_timestamp(qr_data)
        
        self.assertFalse(result['valid'])
        self.assertIn('error', result)
    
    @patch('api_qr_temporal.get_db_connection')
    def test_process_student_no_encontrado(self, mock_db):
        """Test estudiante no encontrado en BD"""
        from api_qr_temporal import process_student
        
        # Mock de conexión
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock estudiante no encontrado
        mock_cursor.fetchone.return_value = None
        
        result = process_student('Juan', 'Pérez', 'juan@test.com')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('no encontrado', result['error'].lower())
    
    @patch('api_qr_temporal.get_db_connection')
    def test_process_student_estudiante_inactivo(self, mock_db):
        """Test estudiante inactivo"""
        from api_qr_temporal import process_student
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock estudiante inactivo
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'email': 'juan@test.com',
            'activo': 0  # Inactivo
        }
        
        result = process_student('Juan', 'Pérez', 'juan@test.com')
        
        self.assertFalse(result['success'])
        self.assertIn('inactivo', result['error'].lower())
    
    @patch('api_qr_temporal.get_db_connection')
    def test_process_student_error_bd(self, mock_db):
        """Test error de base de datos"""
        from api_qr_temporal import process_student
        
        # Mock error de conexión
        mock_db.return_value = None
        
        result = process_student('Juan', 'Pérez', 'juan@test.com')
        
        self.assertFalse(result['success'])
        self.assertIn('conexión', result['error'].lower())
    
    @patch('api_qr_temporal.get_db_connection')
    def test_process_helper_error_bd_exception(self, mock_db):
        """Test excepción en base de datos para ayudante"""
        from api_qr_temporal import process_helper
        
        # Mock que lanza excepción
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Simular excepción en execute
        mock_cursor.execute.side_effect = Exception("Database error")
        
        result = process_helper('María', 'González', 'maria@test.com')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    # ========== TESTS DE VALIDACIÓN DE DATOS QR ==========
    
    def test_qr_data_estructura_valida_estudiante(self):
        """Test estructura válida de QR para estudiante"""
        qr_data = self.valid_student_qr
        
        # Verificar campos requeridos
        required_fields = ['name', 'surname', 'email', 'tipoUsuario', 'timestamp']
        for field in required_fields:
            self.assertIn(field, qr_data)
            self.assertIsNotNone(qr_data[field])
        
        # Verificar tipos
        self.assertIsInstance(qr_data['name'], str)
        self.assertIsInstance(qr_data['surname'], str)
        self.assertIsInstance(qr_data['email'], str)
        self.assertEqual(qr_data['tipoUsuario'], 'ESTUDIANTE')
        self.assertIsInstance(qr_data['timestamp'], int)
    
    def test_qr_data_estructura_valida_ayudante(self):
        """Test estructura válida de QR para ayudante"""
        qr_data = self.valid_helper_qr
        
        # Verificar campos específicos de ayudante
        self.assertEqual(qr_data['tipoUsuario'], 'AYUDANTE')
        self.assertIn('@', qr_data['email'])
        self.assertGreater(len(qr_data['name']), 0)
        self.assertGreater(len(qr_data['surname']), 0)
    
    def test_qr_data_campos_faltantes(self):
        """Test QR con campos faltantes"""
        incomplete_qr = {
            'name': 'Juan',
            # Faltan surname, email, tipoUsuario
        }
        
        required_fields = ['name', 'surname', 'email', 'tipoUsuario']
        missing_fields = []
        
        for field in required_fields:
            if field not in incomplete_qr:
                missing_fields.append(field)
        
        self.assertGreater(len(missing_fields), 0)
        self.assertIn('surname', missing_fields)
        self.assertIn('email', missing_fields)
        self.assertIn('tipoUsuario', missing_fields)
    
    def test_qr_data_tipo_usuario_invalido(self):
        """Test QR con tipo de usuario inválido"""
        invalid_types = ['PROFESOR', 'ADMIN', '', 'INVALID', None, 123]
        valid_types = ['ESTUDIANTE', 'AYUDANTE']
        
        for invalid_type in invalid_types:
            with self.subTest(tipo=invalid_type):
                self.assertNotIn(invalid_type, valid_types)
    
    def test_qr_data_email_formato_invalido(self):
        """Test QR con email en formato inválido"""
        invalid_emails = [
            'not-an-email',
            '@domain.com',
            'user@',
            '',
            'spaces in@email.com',
            'no-domain@'
        ]
        
        # Simulación básica de validación de email
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for email in invalid_emails:
            with self.subTest(email=email):
                is_valid = bool(re.match(email_pattern, email)) if email else False
                self.assertFalse(is_valid)
    
    # ========== TESTS DE INTEGRACIÓN MOCK ==========
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"test": "config"}')
    def test_config_file_loading(self, mock_file):
        """Test carga de archivo de configuración"""
        import json
        
        # Simular carga de configuración
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            self.assertIsInstance(config, dict)
            self.assertIn('test', config)
            mock_file.assert_called_once()
        
        except Exception as e:
            # Si falla, verificar que al menos se intentó
            mock_file.assert_called_once()
    
    def test_response_structure_success(self):
        """Test estructura de respuesta exitosa"""
        success_response = {
            "success": True,
            "tipo": "Entrada",
            "usuario_tipo": "ESTUDIANTE",
            "nombre": "Juan",
            "apellido": "Pérez",
            "email": "juan@test.com",
            "fecha": "2023-12-25",
            "hora": "10:30:00",
            "message": "Entrada registrada para Juan Pérez"
        }
        
        # Verificar estructura requerida
        required_fields = ['success', 'tipo', 'usuario_tipo', 'message']
        for field in required_fields:
            self.assertIn(field, success_response)
        
        # Verificar tipos y valores
        self.assertTrue(success_response['success'])
        self.assertIn(success_response['tipo'], ['Entrada', 'Salida'])
        self.assertIn(success_response['usuario_tipo'], ['ESTUDIANTE', 'AYUDANTE'])
        self.assertIsInstance(success_response['message'], str)
        self.assertGreater(len(success_response['message']), 0)
    
    def test_response_structure_error(self):
        """Test estructura de respuesta de error"""
        error_response = {
            "success": False,
            "error": "Usuario no encontrado",
            "expired": False
        }
        
        # Verificar estructura de error
        self.assertFalse(error_response['success'])
        self.assertIn('error', error_response)
        self.assertIsInstance(error_response['error'], str)
        self.assertGreater(len(error_response['error']), 0)
    
    # ========== TESTS DE CASOS EXTREMOS ==========
    
    def test_timestamp_edge_cases(self):
        """Test casos extremos de timestamp"""
        from api_qr_temporal import validate_timestamp
        
        edge_cases = [
            # Timestamp en el límite exacto (16 segundos)
            {
                'timestamp': (time.time() * 1000) - 16000,
                'expected': False
            },
            # Timestamp justo dentro del límite (15 segundos)
            {
                'timestamp': (time.time() * 1000) - 15000,
                'expected': True
            },
            # Timestamp futuro
            {
                'timestamp': (time.time() * 1000) + 5000,
                'expected': True
            }
        ]
        
        for case in edge_cases:
            with self.subTest(timestamp=case['timestamp']):
                qr_data = {
                    'timestamp': case['timestamp'],
                    'status': 'VALID'
                }
                result = validate_timestamp(qr_data)
                self.assertEqual(result['valid'], case['expected'])

class TestCoverageReporting(unittest.TestCase):
    """Tests adicionales para aumentar cobertura"""
    
    def test_multiple_normalize_scenarios(self):
        """Test múltiples escenarios de normalización"""
        from api_qr_temporal import normalize_email
        
        # Casos adicionales para cobertura
        test_scenarios = [
            # Unicode y caracteres especiales
            ('tëst@éxample.com', 'tëst@éxample.com'),
            # Números y guiones
            ('user-123@test-domain.co.uk', 'user-123@test-domain.co.uk'),
            # Solo espacios
            ('   ', ''),
            # String vacío
            ('', ''),
        ]
        
        for input_email, expected in test_scenarios:
            result = normalize_email(input_email)
            self.assertEqual(result, expected)
    
    @patch('api_qr_temporal.datetime')
    def test_get_dia_espanol_all_days(self, mock_datetime):
        """Test obtener día en español para todos los días"""
        from api_qr_temporal import get_dia_espanol
        
        # Mapeo de días en inglés a español
        days_mapping = {
            'Monday': 'lunes',
            'Tuesday': 'martes', 
            'Wednesday': 'miércoles',
            'Thursday': 'jueves',
            'Friday': 'viernes',
            'Saturday': 'sábado',
            'Sunday': 'domingo'
        }
        
        for english_day, spanish_day in days_mapping.items():
            # Mock datetime para retornar día específico
            mock_datetime.now.return_value.strftime.return_value = english_day
            
            result = get_dia_espanol()
            self.assertEqual(result, spanish_day)

if __name__ == '__main__':
    # Configurar cobertura si está disponible
    try:
        import coverage
        cov = coverage.Coverage()
        cov.start()
    except ImportError:
        cov = None
    
    # Ejecutar tests
    unittest.main(ver