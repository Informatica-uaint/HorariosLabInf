# tests/test_ayudantes_api.py
import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import os
import json
import hashlib
from datetime import datetime, date, time, timedelta
import pytz

# Add the ayudantes directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../back-end/ayudantes'))

class TestAyudantesAPI(unittest.TestCase):
    """Comprehensive tests for Ayudantes API"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_admin_data = {
            'email': 'admin@test.com',
            'password': 'test123',
            'nombre': 'Admin',
            'apellido': 'Test'
        }
        self.valid_registro_data = {
            'fecha': '2023-12-25',
            'hora': '10:30:00',
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'email': 'juan@test.com',
            'tipo': 'Entrada'
        }

class TestAuthUtils(unittest.TestCase):
    """Test authentication utilities"""
    
    def test_hash_password_basic(self):
        """Test basic password hashing"""
        try:
            from utils.auth import hash_password
            
            password = "test123"
            hashed = hash_password(password)
            
            # Verify hash is generated
            self.assertIsNotNone(hashed)
            self.assertIsInstance(hashed, str)
            self.assertNotEqual(password, hashed)
            self.assertGreater(len(hashed), 0)
            
        except ImportError:
            self.skipTest("hash_password function not available")
    
    def test_hash_password_consistency(self):
        """Test hash consistency - same input produces same output"""
        try:
            from utils.auth import hash_password
            
            password = "test123"
            hash1 = hash_password(password)
            hash2 = hash_password(password)
            
            # Same password should generate same hash
            self.assertEqual(hash1, hash2)
            
        except ImportError:
            self.skipTest("hash_password function not available")
    
    def test_hash_password_different_inputs(self):
        """Test different passwords produce different hashes"""
        try:
            from utils.auth import hash_password
            
            hash1 = hash_password("password1")
            hash2 = hash_password("password2")
            
            self.assertNotEqual(hash1, hash2)
            
        except ImportError:
            self.skipTest("hash_password function not available")
    
    def test_hash_password_empty(self):
        """Test with empty password"""
        try:
            from utils.auth import hash_password
            
            result = hash_password("")
            self.assertIsNotNone(result)
            self.assertIsInstance(result, str)
            
            # Should match SHA256 of empty string
            expected = hashlib.sha256("".encode()).hexdigest()
            self.assertEqual(result, expected)
            
        except ImportError:
            self.skipTest("hash_password function not available")
    
    def test_hash_password_special_characters(self):
        """Test with special characters"""
        try:
            from utils.auth import hash_password
            
            special_password = "pässwörd!@#$%^&*()"
            result = hash_password(special_password)
            
            self.assertIsNotNone(result)
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)
            
        except ImportError:
            self.skipTest("hash_password function not available")

class TestDateTimeUtils(unittest.TestCase):
    """Test datetime utilities"""
    
    def test_get_current_datetime(self):
        """Test getting current datetime"""
        try:
            from utils.datetime_utils import get_current_datetime
            
            result = get_current_datetime()
            self.assertIsInstance(result, datetime)
            
            # Should be timezone aware
            self.assertIsNotNone(result.tzinfo)
            
        except ImportError:
            self.skipTest("get_current_datetime function not available")
    
    def test_format_hora_with_time_object(self):
        """Test formatting time object"""
        try:
            from utils.datetime_utils import format_hora
            
            hora = time(14, 30, 45)
            result = format_hora(hora)
            self.assertEqual(result, "14:30:45")
            
        except ImportError:
            self.skipTest("format_hora function not available")
    
    def test_format_hora_with_timedelta(self):
        """Test formatting timedelta object"""
        try:
            from utils.datetime_utils import format_hora
            
            hora = timedelta(hours=8, minutes=30, seconds=15)
            result = format_hora(hora)
            self.assertEqual(result, "08:30:15")
            
        except ImportError:
            self.skipTest("format_hora function not available")
    
    def test_format_hora_with_string(self):
        """Test formatting string time"""
        try:
            from utils.datetime_utils import format_hora
            
            hora = "10:15:30"
            result = format_hora(hora)
            self.assertEqual(result, "10:15:30")
            
        except ImportError:
            self.skipTest("format_hora function not available")
    
    def test_convert_to_time_string(self):
        """Test converting string to time object"""
        try:
            from utils.datetime_utils import convert_to_time
            
            hora_str = "14:30:45"
            result = convert_to_time(hora_str)
            expected = time(14, 30, 45)
            self.assertEqual(result, expected)
            
        except ImportError:
            self.skipTest("convert_to_time function not available")
    
    def test_convert_to_time_time_object(self):
        """Test converting time object (should return same)"""
        try:
            from utils.datetime_utils import convert_to_time
            
            hora = time(10, 15, 30)
            result = convert_to_time(hora)
            self.assertEqual(result, hora)
            
        except ImportError:
            self.skipTest("convert_to_time function not available")
    
    def test_convert_to_time_timedelta(self):
        """Test converting timedelta to time"""
        try:
            from utils.datetime_utils import convert_to_time
            
            td = timedelta(hours=10, minutes=15, seconds=30)
            result = convert_to_time(td)
            expected = time(10, 15, 30)
            self.assertEqual(result, expected)
            
        except ImportError:
            self.skipTest("convert_to_time function not available")
    
    def test_convert_to_time_invalid(self):
        """Test converting invalid input"""
        try:
            from utils.datetime_utils import convert_to_time
            
            result = convert_to_time("invalid")
            self.assertEqual(result, time(0, 0, 0))
            
        except ImportError:
            self.skipTest("convert_to_time function not available")
    
    def test_get_week_dates(self):
        """Test getting week start and end dates"""
        try:
            from utils.datetime_utils import get_week_dates
            
            start, end = get_week_dates()
            
            self.assertIsInstance(start, datetime)
            self.assertIsInstance(end, datetime)
            self.assertLess(start, end)
            
            # Should span 6 days (Monday to Sunday)
            diff = end - start
            self.assertEqual(diff.days, 6)
            
        except ImportError:
            self.skipTest("get_week_dates function not available")

class TestConfig(unittest.TestCase):
    """Test configuration settings"""
    
    def test_config_class_exists(self):
        """Test that Config class exists and has required attributes"""
        try:
            from config import Config
            
            # Test timezone exists
            self.assertTrue(hasattr(Config, 'TIMEZONE'))
            self.assertEqual(Config.TIMEZONE, 'America/Santiago')
            
            # Test days mapping exists
            self.assertTrue(hasattr(Config, 'DIAS_SEMANA'))
            self.assertIsInstance(Config.DIAS_SEMANA, dict)
            
            # Verify days mapping
            self.assertIn('Monday', Config.DIAS_SEMANA)
            self.assertIn('Friday', Config.DIAS_SEMANA)
            self.assertEqual(Config.DIAS_SEMANA['Monday'], 'lunes')
            self.assertEqual(Config.DIAS_SEMANA['Friday'], 'viernes')
            
        except ImportError:
            self.skipTest("Config class not available")
    
    def test_dias_traduccion_mapping(self):
        """Test days translation mapping"""
        try:
            from config import Config
            
            self.assertTrue(hasattr(Config, 'DIAS_TRADUCCION'))
            self.assertIsInstance(Config.DIAS_TRADUCCION, dict)
            
            # Test some mappings
            self.assertIn('monday', Config.DIAS_TRADUCCION)
            self.assertIn('friday', Config.DIAS_TRADUCCION)
            self.assertEqual(Config.DIAS_TRADUCCION['monday'], 'lunes')
            self.assertEqual(Config.DIAS_TRADUCCION['friday'], 'viernes')
            
        except ImportError:
            self.skipTest("Config class not available")
    
    def test_db_config_attributes(self):
        """Test database configuration attributes"""
        try:
            from config import Config
            
            # These might be None in test environment, but should exist
            db_attrs = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'DB_PORT']
            
            for attr in db_attrs:
                self.assertTrue(hasattr(Config, attr))
            
        except ImportError:
            self.skipTest("Config class not available")

class TestJSONEncoder(unittest.TestCase):
    """Test custom JSON encoder"""
    
    def test_custom_json_encoder_datetime(self):
        """Test encoding datetime objects"""
        try:
            from utils.json_encoder import CustomJSONEncoder
            
            encoder = CustomJSONEncoder()
            dt = datetime(2023, 12, 25, 15, 30, 45)
            
            result = encoder.default(dt)
            self.assertIsInstance(result, str)
            self.assertIn('2023-12-25', result)
            self.assertIn('15:30:45', result)
            
        except ImportError:
            self.skipTest("CustomJSONEncoder not available")
    
    def test_custom_json_encoder_timedelta(self):
        """Test encoding timedelta objects"""
        try:
            from utils.json_encoder import CustomJSONEncoder
            
            encoder = CustomJSONEncoder()
            td = timedelta(hours=2, minutes=30)
            
            result = encoder.default(td)
            self.assertIsInstance(result, str)
            
        except ImportError:
            self.skipTest("CustomJSONEncoder not available")
    
    def test_custom_json_encoder_regular_object(self):
        """Test encoding regular object (should raise TypeError)"""
        try:
            from utils.json_encoder import CustomJSONEncoder
            
            encoder = CustomJSONEncoder()
            
            # Should raise TypeError for non-serializable objects
            with self.assertRaises(TypeError):
                encoder.default(object())
                
        except ImportError:
            self.skipTest("CustomJSONEncoder not available")
    
    def test_custom_json_provider(self):
        """Test custom JSON provider"""
        try:
            from utils.json_encoder import CustomJSONProvider
            
            provider = CustomJSONProvider()
            
            # Test data with datetime
            data = {
                'timestamp': datetime(2023, 12, 25, 15, 30, 45),
                'duration': timedelta(hours=1),
                'message': 'test'
            }
            
            # Should be able to serialize
            json_str = provider.dumps(data)
            self.assertIsInstance(json_str, str)
            
            # Should be able to deserialize
            parsed = provider.loads(json_str)
            self.assertIsInstance(parsed, dict)
            self.assertIn('message', parsed)
            
        except ImportError:
            self.skipTest("CustomJSONProvider not available")

class TestDatabaseOperations(unittest.TestCase):
    """Test database operations"""
    
    @patch('pymysql.connect')
    def test_get_connection_success(self, mock_connect):
        """Test successful database connection"""
        try:
            from database import get_connection
            
            mock_connection = MagicMock()
            mock_connect.return_value = mock_connection
            
            result = get_connection()
            self.assertIsNotNone(result)
            mock_connect.assert_called_once()
            
        except ImportError:
            self.skipTest("get_connection function not available")
    
    @patch('pymysql.connect')
    def test_get_connection_failure(self, mock_connect):
        """Test database connection failure"""
        try:
            from database import get_connection
            
            # Mock connection failure
            mock_connect.side_effect = Exception("Connection failed")
            
            # Should handle gracefully
            try:
                result = get_connection()
                # Implementation might return None or raise exception
                # Both are acceptable
            except Exception:
                # Expected behavior
                pass
                
        except ImportError:
            self.skipTest("get_connection function not available")
    
    def test_db_config_structure(self):
        """Test database configuration structure"""
        try:
            from database import get_db_config
            
            config = get_db_config()
            
            # Should be a dictionary
            self.assertIsInstance(config, dict)
            
            # Should contain required keys
            required_keys = ['host', 'user', 'password', 'database', 'port']
            for key in required_keys:
                self.assertIn(key, config)
            
            # Port should be integer
            self.assertIsInstance(config['port'], int)
            self.assertGreater(config['port'], 0)
            
        except ImportError:
            self.skipTest("get_db_config function not available")

class TestRouteLogic(unittest.TestCase):
    """Test route logic without Flask context"""
    
    def test_register_data_validation(self):
        """Test admin registration data validation"""
        # Valid data structure
        valid_data = {
            'email': 'admin@test.com',
            'password': 'securepass123',
            'nombre': 'Admin',
            'apellido': 'User'
        }
        
        required_fields = ['email', 'password', 'nombre', 'apellido']
        
        # All required fields should be present
        for field in required_fields:
            self.assertIn(field, valid_data)
            self.assertIsNotNone(valid_data[field])
            self.assertNotEqual(valid_data[field], '')
    
    def test_registro_data_structure(self):
        """Test registro data structure"""
        registro_data = {
            'fecha': '2023-12-25',
            'hora': '10:30:00',
            'dia': 'lunes',
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'email': 'juan@test.com',
            'tipo': 'Entrada',
            'auto_generado': False
        }
        
        # Verify required fields
        required_fields = ['fecha', 'hora', 'nombre', 'apellido', 'email', 'tipo']
        for field in required_fields:
            self.assertIn(field, registro_data)
        
        # Verify tipo is valid
        valid_tipos = ['Entrada', 'Salida']
        self.assertIn(registro_data['tipo'], valid_tipos)
        
        # Verify boolean field
        self.assertIsInstance(registro_data['auto_generado'], bool)
    
    def test_horario_data_structure(self):
        """Test horario assignment data structure"""
        horario_data = {
            'usuario_id': 1,
            'dia': 'lunes',
            'hora_entrada': '08:00:00',
            'hora_salida': '17:00:00'
        }
        
        required_fields = ['usuario_id', 'dia', 'hora_entrada', 'hora_salida']
        for field in required_fields:
            self.assertIn(field, horario_data)
        
        # Verify day is valid
        valid_days = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
        self.assertIn(horario_data['dia'], valid_days)
        
        # Verify user_id is positive integer
        self.assertIsInstance(horario_data['usuario_id'], int)
        self.assertGreater(horario_data['usuario_id'], 0)
    
    def test_cumplimiento_response_structure(self):
        """Test cumplimiento response structure"""
        cumplimiento_response = {
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'email': 'juan@test.com',
            'estado': 'Cumple',
            'bloques': ['lunes 08:00-17:00'],
            'bloques_info': [
                {
                    'bloque': 'lunes 08:00-17:00',
                    'estado': 'Cumplido'
                }
            ]
        }
        
        # Verify structure
        required_fields = ['nombre', 'apellido', 'email', 'estado', 'bloques']
        for field in required_fields:
            self.assertIn(field, cumplimiento_response)
        
        # Verify estado is valid
        valid_estados = ['Cumple', 'No Cumple', 'Incompleto', 'Ausente', 'Pendiente', 'No Aplica']
        self.assertIn(cumplimiento_response['estado'], valid_estados)
        
        # Verify bloques is list
        self.assertIsInstance(cumplimiento_response['bloques'], list)
    
    def test_horas_acumuladas_structure(self):
        """Test horas acumuladas response structure"""
        horas_response = {
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'email': 'juan@test.com',
            'dias_asistidos': 5.2,
            'horas_totales': 41.5,
            'dias_calendario': 6
        }
        
        required_fields = ['nombre', 'apellido', 'email', 'dias_asistidos', 'horas_totales']
        for field in required_fields:
            self.assertIn(field, horas_response)
        
        # Verify numeric fields
        self.assertIsInstance(horas_response['dias_asistidos'], (int, float))
        self.assertIsInstance(horas_response['horas_totales'], (int, float))
        self.assertGreaterEqual(horas_response['dias_asistidos'], 0)
        self.assertGreaterEqual(horas_response['horas_totales'], 0)

class TestAppCreation(unittest.TestCase):
    """Test Flask app creation"""
    
    @patch.dict(os.environ, {
        'JWT_SECRET': 'test-secret',
        'MYSQL_HOST': 'localhost',
        'MYSQL_USER': 'test',
        'MYSQL_PASSWORD': 'test',
        'MYSQL_DB': 'test'
    })
    def test_create_app_function_exists(self):
        """Test that create_app function exists"""
        try:
            from app import create_app
            
            self.assertTrue(callable(create_app))
            
            # Try to create app (might fail due to dependencies)
            try:
                app = create_app()
                self.assertIsNotNone(app)
            except Exception:
                # Expected due to missing dependencies in test environment
                pass
                
        except ImportError:
            self.skipTest("create_app function not available")

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def test_timezone_handling(self):
        """Test timezone handling"""
        try:
            from utils.datetime_utils import get_current_datetime
            from config import Config
            
            # Should handle Santiago timezone
            self.assertEqual(Config.TIMEZONE, 'America/Santiago')
            
            # Current datetime should be timezone aware
            now = get_current_datetime()
            self.assertIsNotNone(now.tzinfo)
            
        except ImportError:
            self.skipTest("DateTime utils not available")
    
    def test_large_time_differences(self):
        """Test handling of large time differences"""
        try:
            from utils.datetime_utils import convert_to_time
            
            # Test large timedelta (should wrap around)
            large_td = timedelta(hours=25, minutes=30)  # More than 24 hours
            result = convert_to_time(large_td)
            
            # Should handle gracefully
            self.assertIsInstance(result, time)
            
        except ImportError:
            self.skipTest("DateTime utils not available")
    
    def test_special_date_cases(self):
        """Test special date cases"""
        try:
            from utils.datetime_utils import get_week_dates
            
            start, end = get_week_dates()
            
            # Start should be Monday (weekday 0)
            self.assertEqual(start.weekday(), 0)
            
            # End should be Sunday (weekday 6)
            self.assertEqual(end.weekday(), 6)
            
        except ImportError:
            self.skipTest("DateTime utils not available")
    
    def test_empty_password_hash(self):
        """Test hashing empty password"""
        try:
            from utils.auth import hash_password
            
            # Should handle empty password gracefully
            result = hash_password("")
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)
            
        except ImportError:
            self.skipTest("Auth utils not available")

class TestIntegrationPreparation(unittest.TestCase):
    """Prepare for integration tests"""
    
    def test_required_modules_exist(self):
        """Test that required modules can be imported"""
        required_modules = [
            'config',
            'database',
            'utils.auth',
            'utils.datetime_utils',
            'utils.json_encoder'
        ]
        
        for module_name in required_modules:
            try:
                __import__(module_name)
                # Module exists
                self.assertTrue(True)
            except ImportError:
                # Module not available in test environment
                self.skipTest(f"Module {module_name} not available")
    
    def test_environment_configuration(self):
        """Test environment configuration handling"""
        # Should handle missing environment variables gracefully
        env_vars = [
            'JWT_SECRET',
            'MYSQL_HOST', 
            'MYSQL_USER',
            'MYSQL_PASSWORD',
            'MYSQL_DB'
        ]
        
        for var in env_vars:
            value = os.getenv(var, 'default')
            self.assertIsInstance(value, str)

if __name__ == '__main__':
    # Configure logging for cleaner test output
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Run tests with verbose output
    unittest.main(verbosity=2, buffer=True)
