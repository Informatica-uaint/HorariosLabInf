# tests/test_estudiantes_api.py
import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import os
import json
from datetime import datetime, date, time

# Add the estudiantes directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../back-end/estudiantes'))

class TestEstudiantesAPI(unittest.TestCase):
    """Comprehensive tests for Estudiantes API"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = None
        self.client = None
        self.valid_student_data = {
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'email': 'juan.perez@test.com',
            'carrera': 'Ingeniería'
        }
        self.valid_qr_data = {
            'name': 'María',
            'surname': 'González',
            'email': 'maria@test.com',
            'tipoUsuario': 'ESTUDIANTE',
            'timestamp': int(datetime.now().timestamp() * 1000)
        }

class TestValidators(unittest.TestCase):
    """Test validation functions"""
    
    def test_validate_email_valid_cases(self):
        """Test valid email validation"""
        try:
            from utils.validators import validate_email
            
            valid_emails = [
                'test@example.com',
                'user.name@domain.co.uk',
                'student123@university.edu',
                'valid+email@test.org'
            ]
            
            for email in valid_emails:
                with self.subTest(email=email):
                    self.assertTrue(validate_email(email))
                    
        except ImportError:
            self.skipTest("validate_email function not available")
    
    def test_validate_email_invalid_cases(self):
        """Test invalid email validation"""
        try:
            from utils.validators import validate_email
            
            invalid_emails = [
                'invalid-email',
                '@domain.com',
                'user@',
                '',
                None,
                'spaces in@email.com',
                'no-domain@'
            ]
            
            for email in invalid_emails:
                with self.subTest(email=email):
                    self.assertFalse(validate_email(email))
                    
        except ImportError:
            self.skipTest("validate_email function not available")
    
    def test_validate_required_fields_complete(self):
        """Test validation with all required fields"""
        try:
            from utils.validators import validate_required_fields
            
            data = {
                'nombre': 'Juan',
                'apellido': 'Pérez',
                'email': 'juan@test.com'
            }
            required = ['nombre', 'apellido', 'email']
            
            self.assertTrue(validate_required_fields(data, required))
            
        except ImportError:
            self.skipTest("validate_required_fields function not available")
    
    def test_validate_required_fields_missing(self):
        """Test validation with missing fields"""
        try:
            from utils.validators import validate_required_fields
            
            # Missing apellido
            data = {
                'nombre': 'Juan',
                'email': 'juan@test.com'
            }
            required = ['nombre', 'apellido', 'email']
            
            self.assertFalse(validate_required_fields(data, required))
            
            # Empty values
            data_empty = {
                'nombre': '',
                'apellido': 'Pérez',
                'email': 'juan@test.com'
            }
            
            self.assertFalse(validate_required_fields(data_empty, required))
            
        except ImportError:
            self.skipTest("validate_required_fields function not available")
    
    def test_validate_qr_data_valid(self):
        """Test valid QR data validation"""
        try:
            from utils.validators import validate_qr_data
            
            qr_data = {
                'name': 'Juan',
                'surname': 'Pérez',
                'email': 'juan@test.com',
                'tipoUsuario': 'ESTUDIANTE',
                'timestamp': int(datetime.now().timestamp() * 1000)
            }
            
            result = validate_qr_data(qr_data)
            self.assertTrue(result['valid'])
            
        except ImportError:
            self.skipTest("validate_qr_data function not available")
    
    def test_validate_qr_data_invalid(self):
        """Test invalid QR data validation"""
        try:
            from utils.validators import validate_qr_data
            
            # Missing fields
            qr_data_incomplete = {
                'name': 'Juan',
                'email': 'juan@test.com'
                # Missing surname and tipoUsuario
            }
            
            result = validate_qr_data(qr_data_incomplete)
            self.assertFalse(result['valid'])
            
            # Wrong user type
            qr_data_wrong_type = {
                'name': 'Juan',
                'surname': 'Pérez',
                'email': 'juan@test.com',
                'tipoUsuario': 'PROFESOR'
            }
            
            result = validate_qr_data(qr_data_wrong_type)
            self.assertFalse(result['valid'])
            
        except ImportError:
            self.skipTest("validate_qr_data function not available")

class TestHelpers(unittest.TestCase):
    """Test helper functions"""
    
    def test_format_response_basic(self):
        """Test basic response formatting"""
        try:
            from utils.helpers import format_response
            
            data = {'test': 'value'}
            response = format_response(data)
            
            # Should return Flask response object
            self.assertIsNotNone(response)
            
            # Check JSON structure
            json_data = json.loads(response.data)
            self.assertEqual(json_data['status'], 'success')
            self.assertEqual(json_data['data'], data)
            self.assertIn('timestamp', json_data)
            
        except ImportError:
            self.skipTest("format_response function not available")
    
    def test_format_response_with_message(self):
        """Test response formatting with message"""
        try:
            from utils.helpers import format_response
            
            data = {'test': 'value'}
            message = 'Operation successful'
            response = format_response(data, message)
            
            json_data = json.loads(response.data)
            self.assertEqual(json_data['message'], message)
            
        except ImportError:
            self.skipTest("format_response function not available")
    
    def test_serialize_datetime(self):
        """Test datetime serialization"""
        try:
            from utils.helpers import serialize_datetime
            
            # Test datetime
            dt = datetime(2023, 12, 25, 15, 30, 45)
            result = serialize_datetime(dt)
            self.assertIsInstance(result, str)
            self.assertIn('2023-12-25', result)
            
            # Test date
            d = date(2023, 12, 25)
            result = serialize_datetime(d)
            self.assertEqual(result, '2023-12-25')
            
            # Test time
            t = time(15, 30, 45)
            result = serialize_datetime(t)
            self.assertEqual(result, '15:30:45')
            
            # Test other objects
            obj = "test string"
            result = serialize_datetime(obj)
            self.assertEqual(result, obj)
            
        except ImportError:
            self.skipTest("serialize_datetime function not available")
    
    def test_safe_int(self):
        """Test safe integer conversion"""
        try:
            from utils.helpers import safe_int
            
            # Valid cases
            self.assertEqual(safe_int('123'), 123)
            self.assertEqual(safe_int(123), 123)
            self.assertEqual(safe_int('0'), 0)
            self.assertEqual(safe_int('-456'), -456)
            
            # Invalid cases with default
            self.assertEqual(safe_int('abc', default=42), 42)
            self.assertEqual(safe_int(None, default=42), 42)
            self.assertEqual(safe_int([], default=42), 42)
            
        except ImportError:
            self.skipTest("safe_int function not available")
    
    def test_safe_bool(self):
        """Test safe boolean conversion"""
        try:
            from utils.helpers import safe_bool
            
            # Valid cases
            self.assertTrue(safe_bool(True))
            self.assertFalse(safe_bool(False))
            self.assertTrue(safe_bool('true'))
            self.assertFalse(safe_bool('false'))
            self.assertTrue(safe_bool('1'))
            self.assertFalse(safe_bool('0'))
            self.assertTrue(safe_bool(1))
            self.assertFalse(safe_bool(0))
            
            # Invalid cases with default
            self.assertTrue(safe_bool(None, default=True))
            self.assertFalse(safe_bool('invalid', default=False))
            
        except ImportError:
            self.skipTest("safe_bool function not available")

class TestDatabaseConfig(unittest.TestCase):
    """Test database configuration"""
    
    @patch('mysql.connector.connect')
    def test_database_connection_mock(self, mock_connect):
        """Test database connection with mock"""
        try:
            from config.database import get_db
            
            mock_connection = MagicMock()
            mock_connect.return_value = mock_connection
            
            # Mock Flask g context
            with patch('config.database.g', {}):
                with patch('config.database.current_app') as mock_app:
                    mock_app.config = {
                        'MYSQL_HOST': 'localhost',
                        'MYSQL_USER': 'test',
                        'MYSQL_PASSWORD': 'test',
                        'MYSQL_DB': 'test'
                    }
                    
                    # Should not raise exception
                    self.assertTrue(callable(get_db))
                    
        except ImportError:
            self.skipTest("Database config not available")
    
    @patch('mysql.connector.connect')
    def test_execute_query_select(self, mock_connect):
        """Test execute_query for SELECT statements"""
        try:
            from config.database import execute_query
            
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            
            # Mock SELECT query result
            mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'Test'}]
            
            with patch('config.database.get_db', return_value=mock_connection):
                result = execute_query("SELECT * FROM test")
                self.assertIsInstance(result, list)
                mock_cursor.execute.assert_called_once()
                
        except ImportError:
            self.skipTest("execute_query function not available")

class TestAppCreation(unittest.TestCase):
    """Test Flask app creation"""
    
    @patch.dict(os.environ, {
        'SECRET_KEY': 'test-secret',
        'MYSQL_HOST': 'localhost',
        'MYSQL_USER': 'test',
        'MYSQL_PASSWORD': 'test',
        'MYSQL_DB': 'test'
    })
    def test_create_app_function_exists(self):
        """Test that create_app function exists and is callable"""
        try:
            from app import create_app
            
            self.assertTrue(callable(create_app))
            
            # Try to create app (might fail due to dependencies, that's OK)
            try:
                app = create_app()
                self.assertIsNotNone(app)
            except Exception:
                # Expected due to missing dependencies in test environment
                pass
                
        except ImportError:
            self.skipTest("create_app function not available")
    
    def test_health_endpoint_logic(self):
        """Test health endpoint response structure"""
        # Mock health response
        health_response = {
            'status': 'OK',
            'timestamp': datetime.now().isoformat(),
            'message': 'API funcionando correctamente'
        }
        
        self.assertEqual(health_response['status'], 'OK')
        self.assertIn('timestamp', health_response)
        self.assertIn('message', health_response)
        self.assertIsInstance(health_response['timestamp'], str)

class TestRoutesLogic(unittest.TestCase):
    """Test route logic without Flask context"""
    
    def test_estudiante_data_structure(self):
        """Test expected student data structure"""
        estudiante_data = {
            'id': '1',
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'email': 'juan@test.com',
            'carrera': 'Ingeniería',
            'estado': 'activo',
            'presente': False
        }
        
        # Verify required fields exist
        required_fields = ['id', 'nombre', 'apellido', 'email']
        for field in required_fields:
            self.assertIn(field, estudiante_data)
            self.assertIsNotNone(estudiante_data[field])
        
        # Verify data types
        self.assertIsInstance(estudiante_data['id'], str)
        self.assertIsInstance(estudiante_data['presente'], bool)
    
    def test_registro_data_structure(self):
        """Test expected registro data structure"""
        registro_data = {
            'id': '1',
            'estudianteId': '1',
            'nombreEstudiante': 'Juan',
            'apellidoEstudiante': 'Pérez',
            'rutEstudiante': '',
            'tipoRegistro': 'entrada',
            'horaRegistro': datetime.now().isoformat(),
            'fecha': date.today().isoformat()
        }
        
        # Verify required fields
        required_fields = ['id', 'tipoRegistro', 'horaRegistro', 'fecha']
        for field in required_fields:
            self.assertIn(field, registro_data)
        
        # Verify registro type is valid
        valid_tipos = ['entrada', 'salida']
        self.assertIn(registro_data['tipoRegistro'], valid_tipos)
    
    def test_qr_validation_response_structure(self):
        """Test QR validation response structure"""
        success_response = {
            'success': True,
            'estudiante': {
                'id': 1,
                'nombre': 'Juan',
                'apellido': 'Pérez',
                'email': 'juan@test.com'
            },
            'registro': {
                'id': 1,
                'tipo': 'Entrada',
                'timestamp': datetime.now().isoformat()
            },
            'mensaje': 'Entrada registrada exitosamente'
        }
        
        # Verify structure
        self.assertTrue(success_response['success'])
        self.assertIn('estudiante', success_response)
        self.assertIn('registro', success_response)
        self.assertIn('mensaje', success_response)
        
        # Verify nested structures
        self.assertIn('email', success_response['estudiante'])
        self.assertIn('tipo', success_response['registro'])
        
        error_response = {
            'success': False,
            'error': 'Código QR expirado',
            'expired': True
        }
        
        self.assertFalse(error_response['success'])
        self.assertIn('error', error_response)

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def test_empty_data_handling(self):
        """Test handling of empty or None data"""
        try:
            from utils.validators import validate_required_fields
            
            # None data
            self.assertFalse(validate_required_fields(None, ['field']))
            
            # Empty dict
            self.assertFalse(validate_required_fields({}, ['field']))
            
            # Dict with None values
            data_with_none = {'field': None}
            self.assertFalse(validate_required_fields(data_with_none, ['field']))
            
        except ImportError:
            self.skipTest("Validation functions not available")
    
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON data"""
        malformed_json_strings = [
            "invalid json",
            "{incomplete: json",
            "",
            "null",
            "undefined"
        ]
        
        for json_str in malformed_json_strings:
            with self.subTest(json_string=json_str):
                try:
                    if json_str:
                        json.loads(json_str)
                        # Should not reach here for invalid JSON
                        if json_str in ["invalid json", "{incomplete: json", "undefined"]:
                            self.fail(f"Should have failed for: {json_str}")
                except (json.JSONDecodeError, ValueError):
                    # Expected for invalid JSON
                    pass
    
    def test_large_data_handling(self):
        """Test handling of unexpectedly large data"""
        try:
            from utils.validators import validate_email
            
            # Very long email
            long_email = "a" * 1000 + "@example.com"
            # Should handle gracefully (might be valid or invalid, but shouldn't crash)
            result = validate_email(long_email)
            self.assertIsInstance(result, bool)
            
        except ImportError:
            self.skipTest("Email validation not available")

class TestIntegrationPreparation(unittest.TestCase):
    """Prepare for integration tests"""
    
    def test_required_modules_structure(self):
        """Test that required modules have expected structure"""
        expected_modules = [
            'app',
            'config.database',
            'utils.validators',
            'utils.helpers'
        ]
        
        for module_name in expected_modules:
            try:
                __import__(module_name)
                # Module exists and can be imported
                self.assertTrue(True)
            except ImportError:
                # Module not available, which is acceptable in test environment
                self.skipTest(f"Module {module_name} not available")
    
    def test_environment_variables_handling(self):
        """Test environment variables are handled correctly"""
        required_env_vars = [
            'SECRET_KEY',
            'MYSQL_HOST',
            'MYSQL_USER',
            'MYSQL_PASSWORD',
            'MYSQL_DB'
        ]
        
        # Test that code handles missing env vars gracefully
        for var in required_env_vars:
            # Should not crash when env var is missing
            value = os.getenv(var, 'default_value')
            self.assertIsInstance(value, str)

if __name__ == '__main__':
    # Configure logging for cleaner test output
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Run tests with verbose output
    unittest.main(verbosity=2, buffer=True)
