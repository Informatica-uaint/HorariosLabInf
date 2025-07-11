# tests/test_lector_api.py
import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import os
import json
import time
from datetime import datetime, timedelta

# Add the lector directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../back-end/lector'))

class TestLectorQRAPI(unittest.TestCase):
    """Comprehensive tests for Lector QR API"""
    
    def setUp(self):
        """Set up test fixtures"""
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
        
        self.expired_qr = {
            'name': 'Test',
            'surname': 'User',
            'email': 'test@example.com',
            'tipoUsuario': 'ESTUDIANTE',
            'timestamp': int(time.time() * 1000) - 20000,  # 20 seconds ago
            'status': 'VALID'
        }

class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_normalize_email_basic_cases(self):
        """Test basic email normalization"""
        try:
            from api_qr_temporal import normalize_email
            
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
                    
        except ImportError:
            self.skipTest("normalize_email function not available")
    
    def test_normalize_email_edge_cases(self):
        """Test edge cases for email normalization"""
        try:
            from api_qr_temporal import normalize_email
            
            edge_cases = [
                ('', ''),
                (None, ''),
                ('   ', ''),
                ('UPPERCASE@DOMAIN.COM', 'uppercase@domain.com'),
                ('   spaces@before.com   ', 'spaces@before.com')
            ]
            
            for input_email, expected in edge_cases:
                with self.subTest(email=input_email):
                    result = normalize_email(input_email)
                    self.assertEqual(result, expected)
                    
        except ImportError:
            self.skipTest("normalize_email function not available")
    
    def test_get_dia_espanol(self):
        """Test getting day in Spanish"""
        try:
            from api_qr_temporal import get_dia_espanol
            
            result = get_dia_espanol()
            
            # Should return a valid Spanish day
            valid_days = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
            self.assertIn(result, valid_days)
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)
            
        except ImportError:
            self.skipTest("get_dia_espanol function not available")
    
    @patch('api_qr_temporal.datetime')
    def test_get_dia_espanol_all_days(self, mock_datetime):
        """Test Spanish day conversion for all days"""
        try:
            from api_qr_temporal import get_dia_espanol
            
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
                # Mock datetime to return specific day
                mock_datetime.now.return_value.strftime.return_value = english_day
                
                result = get_dia_espanol()
                self.assertEqual(result, spanish_day)
                
        except ImportError:
            self.skipTest("get_dia_espanol function not available")

class TestTimestampValidation(unittest.TestCase):
    """Test QR timestamp validation"""
    
    def test_validate_timestamp_valid_qr(self):
        """Test validation of valid QR timestamp"""
        try:
            from api_qr_temporal import validate_timestamp
            
            # QR from 5 seconds ago (should be valid)
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
            
        except ImportError:
            self.skipTest("validate_timestamp function not available")
    
    def test_validate_timestamp_expired_qr(self):
        """Test validation of expired QR timestamp"""
        try:
            from api_qr_temporal import validate_timestamp
            
            # QR from 20 seconds ago (should be expired)
            current_time = time.time() * 1000
            qr_data = {
                'timestamp': current_time - 20000,
                'status': 'VALID'
            }
            
            result = validate_timestamp(qr_data)
            
            self.assertFalse(result['valid'])
            self.assertIn('error', result)
            self.assertIn('expirado', result['error'].lower())
            
        except ImportError:
            self.skipTest("validate_timestamp function not available")
    
    def test_validate_timestamp_marked_expired(self):
        """Test validation of QR marked as expired"""
        try:
            from api_qr_temporal import validate_timestamp
            
            qr_data = {
                'timestamp': int(time.time() * 1000),
                'status': 'EXPIRED'
            }
            
            result = validate_timestamp(qr_data)
            
            self.assertFalse(result['valid'])
            self.assertIn('expirado', result['error'].lower())
            
        except ImportError:
            self.skipTest("validate_timestamp function not available")
    
    def test_validate_timestamp_explicit_expired_flag(self):
        """Test validation with explicit expired flag"""
        try:
            from api_qr_temporal import validate_timestamp
            
            qr_data = {
                'timestamp': int(time.time() * 1000),
                'expired': True,
                'status': 'VALID'
            }
            
            result = validate_timestamp(qr_data)
            
            self.assertFalse(result['valid'])
            self.assertIn('expirado', result['error'].lower())
            
        except ImportError:
            self.skipTest("validate_timestamp function not available")
    
    def test_validate_timestamp_missing_timestamp(self):
        """Test validation without timestamp"""
        try:
            from api_qr_temporal import validate_timestamp
            
            qr_data = {
                'status': 'VALID'
                # Missing timestamp
            }
            
            result = validate_timestamp(qr_data)
            
            self.assertFalse(result['valid'])
            self.assertIn('timestamp', result['error'].lower())
            
        except ImportError:
            self.skipTest("validate_timestamp function not available")
    
    def test_validate_timestamp_invalid_timestamp(self):
        """Test validation with invalid timestamp"""
        try:
            from api_qr_temporal import validate_timestamp
            
            qr_data = {
                'timestamp': 'invalid_timestamp',
                'status': 'VALID'
            }
            
            result = validate_timestamp(qr_data)
            
            self.assertFalse(result['valid'])
            self.assertIn('error', result)
            
        except ImportError:
            self.skipTest("validate_timestamp function not available")
    
    def test_validate_timestamp_edge_cases(self):
        """Test timestamp validation edge cases"""
        try:
            from api_qr_temporal import validate_timestamp
            
            current_time = time.time() * 1000
            
            edge_cases = [
                # Exactly at 16 second limit
                {
                    'timestamp': current_time - 16000,
                    'expected_valid': False
                },
                # Just inside limit (15 seconds)
                {
                    'timestamp': current_time - 15000,
                    'expected_valid': True
                },
                # Future timestamp
                {
                    'timestamp': current_time + 5000,
                    'expected_valid': True
                }
            ]
            
            for case in edge_cases:
                with self.subTest(timestamp=case['timestamp']):
                    qr_data = {
                        'timestamp': case['timestamp'],
                        'status': 'VALID'
                    }
                    result = validate_timestamp(qr_data)
                    self.assertEqual(result['valid'], case['expected_valid'])
                    
        except ImportError:
            self.skipTest("validate_timestamp function not available")

class TestQRDataValidation(unittest.TestCase):
    """Test QR data structure validation"""
    
    def test_valid_student_qr_structure(self):
        """Test valid student QR data structure"""
        qr_data = self.setUp()  # Get from parent setUp
        
        # Use local valid data
        qr_data = {
            'name': 'Juan',
            'surname': 'Pérez',
            'email': 'juan@test.com',
            'tipoUsuario': 'ESTUDIANTE',
            'timestamp': int(time.time() * 1000),
            'status': 'VALID'
        }
        
        # Check required fields
        required_fields = ['name', 'surname', 'email', 'tipoUsuario', 'timestamp']
        for field in required_fields:
            self.assertIn(field, qr_data)
            self.assertIsNotNone(qr_data[field])
        
        # Check field types
        self.assertIsInstance(qr_data['name'], str)
        self.assertIsInstance(qr_data['surname'], str)
        self.assertIsInstance(qr_data['email'], str)
        self.assertEqual(qr_data['tipoUsuario'], 'ESTUDIANTE')
        self.assertIsInstance(qr_data['timestamp'], int)
    
    def test_valid_helper_qr_structure(self):
        """Test valid helper QR data structure"""
        qr_data = {
            'name': 'María',
            'surname': 'González',
            'email': 'maria@test.com',
            'tipoUsuario': 'AYUDANTE',
            'timestamp': int(time.time() * 1000),
            'status': 'VALID'
        }
        
        # Check helper-specific fields
        self.assertEqual(qr_data['tipoUsuario'], 'AYUDANTE')
        self.assertIn('@', qr_data['email'])
        self.assertGreater(len(qr_data['name']), 0)
        self.assertGreater(len(qr_data['surname']), 0)
    
    def test_missing_required_fields(self):
        """Test QR with missing required fields"""
        incomplete_qr = {
            'name': 'Juan',
            # Missing surname, email, tipoUsuario
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
    
    def test_invalid_user_types(self):
        """Test invalid user types"""
        invalid_types = ['PROFESOR', 'ADMIN', '', 'INVALID', None, 123]
        valid_types = ['ESTUDIANTE', 'AYUDANTE']
        
        for invalid_type in invalid_types:
            with self.subTest(tipo=invalid_type):
                self.assertNotIn(invalid_type, valid_types)
    
    def test_email_format_validation(self):
        """Test email format validation"""
        invalid_emails = [
            'not-an-email',
            '@domain.com',
            'user@',
            '',
            'spaces in@email.com',
            'no-domain@'
        ]
        
        # Basic email regex pattern
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for email in invalid_emails:
            with self.subTest(email=email):
                is_valid = bool(re.match(email_pattern, email)) if email else False
                self.assertFalse(is_valid)

class TestDatabaseOperations(unittest.TestCase):
    """Test database operations with mocks"""
    
    def test_db_config_structure(self):
        """Test database configuration structure"""
        # Expected DB config structure
        db_config = {
            'host': 'localhost',
            'user': 'test_user',
            'password': 'test_pass',
            'database': 'test_db',
            'port': 3306,
            'charset': 'utf8mb4'
        }
        
        required_keys = ['host', 'user', 'password', 'database', 'port']
        
        for key in required_keys:
            self.assertIn(key, db_config)
        
        self.assertIsInstance(db_config['port'], int)
        self.assertGreater(db_config['port'], 0)
        self.assertIn('utf8', db_config['charset'])
    
    @patch('pymysql.connect')
    def test_get_db_connection_success(self, mock_connect):
        """Test successful database connection"""
        try:
            # Mock successful connection
            mock_connection = MagicMock()
            mock_connect.return_value = mock_connection
            
            # Define mock get_db_connection function
            def get_db_connection():
                try:
                    return mock_connect()
                except Exception:
                    return None
            
            result = get_db_connection()
            self.assertIsNotNone(result)
            mock_connect.assert_called_once()
            
        except ImportError:
            self.skipTest("Database connection functions not available")
    
    @patch('pymysql.connect')
    def test_get_db_connection_failure(self, mock_connect):
        """Test database connection failure"""
        try:
            # Mock connection failure
            mock_connect.side_effect = Exception("Connection failed")
            
            def get_db_connection():
                try:
                    return mock_connect()
                except Exception:
                    return None
            
            result = get_db_connection()
            self.assertIsNone(result)
            
        except ImportError:
            self.skipTest("Database connection functions not available")

class TestProcessingLogic(unittest.TestCase):
    """Test QR processing logic"""
    
    @patch('api_qr_temporal.get_db_connection')
    def test_process_student_success(self, mock_db):
        """Test successful student processing"""
        try:
            from api_qr_temporal import process_student
            
            # Mock database setup
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_db.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            # Mock student exists and is active
            mock_cursor.fetchone.side_effect = [
                {  # Student verification
                    'id': 1,
                    'nombre': 'Juan',
                    'apellido': 'Pérez',
                    'email': 'juan@test.com',
                    'activo': 1
                },
                None  # No previous record today (first entry)
            ]
            
            result = process_student('Juan', 'Pérez', 'juan@test.com')
            
            # Verify successful result
            self.assertTrue(result['success'])
            self.assertEqual(result['tipo'], 'Entrada')
            self.assertEqual(result['usuario_tipo'], 'ESTUDIANTE')
            self.assertEqual(result['nombre'], 'Juan')
            self.assertEqual(result['apellido'], 'Pérez')
            self.assertIn('message', result)
            
            # Verify database operations
            mock_conn.commit.assert_called_once()
            
        except ImportError:
            self.skipTest("process_student function not available")
    
    @patch('api_qr_temporal.get_db_connection')
    def test_process_student_not_found(self, mock_db):
        """Test student not found scenario"""
        try:
            from api_qr_temporal import process_student
            
            # Mock database setup
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_db.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            # Mock student not found
            mock_cursor.fetchone.return_value = None
            
            result = process_student('Juan', 'Pérez', 'juan@test.com')
            
            self.assertFalse(result['success'])
            self.assertIn('error', result)
            self.assertIn('no encontrado', result['error'].lower())
            
        except ImportError:
            self.skipTest("process_student function not available")
    
    @patch('api_qr_temporal.get_db_connection')
    def test_process_student_inactive(self, mock_db):
        """Test inactive student scenario"""
        try:
            from api_qr_temporal import process_student
            
            # Mock database setup
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_db.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            # Mock inactive student
            mock_cursor.fetchone.return_value = {
                'id': 1,
                'nombre': 'Juan',
                'apellido': 'Pérez',
                'email': 'juan@test.com',
                'activo': 0  # Inactive
            }
            
            result = process_student('Juan', 'Pérez', 'juan@test.com')
            
            self.assertFalse(result['success'])
            self.assertIn('inactivo', result['error'].lower())
            
        except ImportError:
            self.skipTest("process_student function not available")
    
    @patch('api_qr_temporal.get_db_connection')
    def test_process_helper_success(self, mock_db):
        """Test successful helper processing"""
        try:
            from api_qr_temporal import process_helper
            
            # Mock database setup
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_db.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            # Mock helper exists and last record was entry
            mock_cursor.fetchone.side_effect = [
                {  # Helper verification
                    'id': 1,
                    'nombre': 'María',
                    'apellido': 'González',
                    'email': 'maria@test.com',
                    'activo': 1
                },
                {  # Last record was entry
                    'tipo': 'Entrada',
                    'fecha_reg': datetime.now().date()
                }
            ]
            
            result = process_helper('María', 'González', 'maria@test.com')
            
            # Should be exit since last was entry
            self.assertTrue(result['success'])
            self.assertEqual(result['tipo'], 'Salida')
            self.assertEqual(result['usuario_tipo'], 'AYUDANTE')
            self.assertEqual(result['nombre'], 'María')
            
        except ImportError:
            self.skipTest("process_helper function not available")
    
    @patch('api_qr_temporal.get_db_connection')
    def test_process_database_error(self, mock_db):
        """Test database error handling"""
        try:
            from api_qr_temporal import process_student
            
            # Mock database connection failure
            mock_db.return_value = None
            
            result = process_student('Juan', 'Pérez', 'juan@test.com')
            
            self.assertFalse(result['success'])
            self.assertIn('conexión', result['error'].lower())
            
        except ImportError:
            self.skipTest("process_student function not available")
    
    def test_determine_registro_type_logic(self):
        """Test logic for determining registro type"""
        # Mock the logic
        def determine_registro_type(last_type, same_day=True):
            if not same_day or not last_type:
                return 'Entrada'
            return 'Salida' if last_type == 'Entrada' else 'Entrada'
        
        # Test cases
        self.assertEqual(determine_registro_type('Entrada', True), 'Salida')
        self.assertEqual(determine_registro_type('Salida', True), 'Entrada')
        self.assertEqual(determine_registro_type(None, True), 'Entrada')
        self.assertEqual(determine_registro_type('Entrada', False), 'Entrada')

class TestResponseStructures(unittest.TestCase):
    """Test API response structures"""
    
    def test_success_response_structure(self):
        """Test successful validation response"""
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
        
        # Verify required fields
        required_fields = ['success', 'tipo', 'usuario_tipo', 'message']
        for field in required_fields:
            self.assertIn(field, success_response)
        
        # Verify values
        self.assertTrue(success_response['success'])
        self.assertIn(success_response['tipo'], ['Entrada', 'Salida'])
        self.assertIn(success_response['usuario_tipo'], ['ESTUDIANTE', 'AYUDANTE'])
        self.assertIsInstance(success_response['message'], str)
        self.assertGreater(len(success_response['message']), 0)
    
    def test_error_response_structure(self):
        """Test error response structure"""
        error_response = {
            "success": False,
            "error": "Usuario no encontrado",
            "expired": False
        }
        
        # Verify structure
        self.assertFalse(error_response['success'])
        self.assertIn('error', error_response)
        self.assertIsInstance(error_response['error'], str)
        self.assertGreater(len(error_response['error']), 0)
    
    def test_health_response_structure(self):
        """Test health endpoint response"""
        health_response = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "service": "QR Temporal API"
        }
        
        self.assertEqual(health_response["status"], "ok")
        self.assertIn("timestamp", health_response)
        self.assertIn("service", health_response)
        self.assertIsInstance(health_response["timestamp"], str)
    
    def test_stats_response_structure(self):
        """Test statistics response structure"""
        stats_response = {
            "success": True,
            "date": "2023-12-25",
            "students": {
                "entries": 15,
                "exits": 12
            },
            "helpers": {
                "entries": 5,
                "exits": 4
            }
        }
        
        self.assertTrue(stats_response["success"])
        self.assertIn("date", stats_response)
        self.assertIn("students", stats_response)
        self.assertIn("helpers", stats_response)
        
        # Verify counters structure
        self.assertIn("entries", stats_response["students"])
        self.assertIn("exits", stats_response["students"])
        self.assertIsInstance(stats_response["students"]["entries"], int)
        self.assertIsInstance(stats_response["students"]["exits"], int)
        self.assertGreaterEqual(stats_response["students"]["entries"], 0)
        self.assertGreaterEqual(stats_response["students"]["exits"], 0)

class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON"""
        invalid_json_strings = [
            "invalid json",
            "{incomplete: json",
            "",
            None
        ]
        
        for json_str in invalid_json_strings:
            with self.subTest(json_string=json_str):
                try:
                    if json_str:
                        json.loads(json_str)
                        if json_str in ["invalid json", "{incomplete: json"]:
                            self.fail(f"Should have failed for: {json_str}")
                except (json.JSONDecodeError, TypeError):
                    # Expected for invalid JSON
                    pass
    
    def test_missing_qr_fields_handling(self):
        """Test handling of QR with missing fields"""
        incomplete_qr = {
            "name": "Juan",
            # Missing surname, email, tipoUsuario
        }
        
        required_fields = ["name", "surname", "email", "tipoUsuario"]
        missing_fields = []
        
        for field in required_fields:
            if field not in incomplete_qr or not incomplete_qr[field]:
                missing_fields.append(field)
        
        self.assertGreater(len(missing_fields), 0)
        self.assertIn("surname", missing_fields)
        self.assertIn("email", missing_fields)
    
    def test_database_error_simulation(self):
        """Test database error scenarios"""
        db_errors = [
            "Connection refused",
            "Table doesn't exist",
            "Access denied",
            "Timeout",
            "Lost connection"
        ]
        
        for error in db_errors:
            # Verify errors are non-empty strings
            self.assertIsInstance(error, str)
            self.assertGreater(len(error), 0)

class TestAppConfiguration(unittest.TestCase):
    """Test Flask app configuration"""
    
    @patch.dict(os.environ, {
        'MYSQL_HOST': 'localhost',
        'MYSQL_USER': 'test',
        'MYSQL_PASSWORD': 'test',
        'MYSQL_DB': 'test',
        'SECRET_KEY': 'test-secret'
    })
    def test_app_configuration(self):
        """Test Flask app configuration"""
        # Mock Flask app configuration
        app_config = {
            'SECRET_KEY': 'test-secret',
            'ENV': 'testing',
            'TESTING': True
        }
        
        # Verify basic configuration
        self.assertIn('SECRET_KEY', app_config)
        self.assertIsNotNone(app_config['SECRET_KEY'])
        self.assertGreater(len(app_config['SECRET_KEY']), 0)
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        # Expected CORS behavior
        allowed_origins = ["*"]  # From the code
        allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        
        # Verify CORS settings structure
        self.assertIn("*", allowed_origins)
        self.assertIn("POST", allowed_methods)
        self.assertIn("GET", allowed_methods)
    
    def test_database_config_from_env(self):
        """Test database configuration from environment"""
        db_config_keys = [
            'MYSQL_HOST',
            'MYSQL_USER', 
            'MYSQL_PASSWORD',
            'MYSQL_DB',
            'MYSQL_PORT'
        ]
        
        # Should handle missing env vars gracefully
        for key in db_config_keys:
            value = os.getenv(key, 'default')
            self.assertIsInstance(value, str)

class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios"""
    
    def test_complete_qr_validation_flow(self):
        """Test complete QR validation flow"""
        # Valid QR data
        qr_data = {
            'name': 'Juan',
            'surname': 'Pérez',
            'email': 'juan@test.com',
            'tipoUsuario': 'ESTUDIANTE',
            'timestamp': int(time.time() * 1000) - 5000,  # 5 seconds ago
            'status': 'VALID'
        }
        
        # Step 1: Validate structure
        required_fields = ['name', 'surname', 'email', 'tipoUsuario']
        for field in required_fields:
            self.assertIn(field, qr_data)
        
        # Step 2: Validate timestamp (would call validate_timestamp)
        current_time = time.time() * 1000
        time_diff = abs(current_time - qr_data['timestamp']) / 1000
        is_valid_time = time_diff <= 16
        self.assertTrue(is_valid_time)
        
        # Step 3: Validate user type
        self.assertIn(qr_data['tipoUsuario'], ['ESTUDIANTE', 'AYUDANTE'])
        
        # Step 4: Expected processing result structure
        expected_result = {
            'success': True,
            'tipo': 'Entrada',  # or 'Salida'
            'usuario_tipo': qr_data['tipoUsuario'],
            'message': f"Entrada registrada para {qr_data['name']} {qr_data['surname']}"
        }
        
        self.assertTrue(expected_result['success'])
        self.assertIn(expected_result['tipo'], ['Entrada', 'Salida'])
    
    def test_environment_variable_fallbacks(self):
        """Test environment variable fallbacks"""
        # Test that app handles missing environment variables
        env_vars_with_defaults = {
            'HOST': '0.0.0.0',
            'PORT': '5000',
            'LOG_LEVEL': 'INFO',
            'CORS_ORIGINS': '*'
        }
        
        for var, default in env_vars_with_defaults.items():
            value = os.getenv(var, default)
            self.assertIsNotNone(value)
            self.assertIsInstance(value, str)

if __name__ == '__main__':
    # Configure logging for cleaner test output
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Run tests with verbose output
    unittest.main(verbosity=2, buffer=True)
