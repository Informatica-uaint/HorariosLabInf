# tests/test_config.py
"""
Test Configuration for HorariosLabInf Back-end APIs
Centralizes test settings and utilities
"""

import os
import sys
from pathlib import Path

# ========================================
# PATH CONFIGURATION
# ========================================

# Get the tests directory
TESTS_DIR = Path(__file__).parent
PROJECT_ROOT = TESTS_DIR.parent

# Back-end API paths
ESTUDIANTES_PATH = PROJECT_ROOT / "back-end" / "estudiantes"
AYUDANTES_PATH = PROJECT_ROOT / "back-end" / "ayudantes"
LECTOR_PATH = PROJECT_ROOT / "back-end" / "lector"

# Add paths to Python path for imports
API_PATHS = [
    str(ESTUDIANTES_PATH),
    str(AYUDANTES_PATH), 
    str(LECTOR_PATH),
    str(TESTS_DIR)
]

def setup_test_paths():
    """Add API paths to sys.path for testing"""
    for path in API_PATHS:
        if path not in sys.path:
            sys.path.insert(0, path)

# ========================================
# TEST ENVIRONMENT CONFIGURATION
# ========================================

# Default test environment variables
DEFAULT_TEST_ENV = {
    # Common Flask settings
    'FLASK_ENV': 'testing',
    'TESTING': 'True',
    'SECRET_KEY': 'test-secret-key-horarios-lab-inf',
    
    # Database settings (mock)
    'MYSQL_HOST': 'localhost',
    'MYSQL_USER': 'test_user',
    'MYSQL_PASSWORD': 'test_password',
    'MYSQL_DB': 'test_database',
    'MYSQL_PORT': '3306',
    'DB_CHARSET': 'utf8mb4',
    
    # JWT settings
    'JWT_SECRET': 'test-jwt-secret-horarios-lab-inf',
    
    # Timezone
    'TZ': 'America/Santiago',
    
    # Logging
    'LOG_LEVEL': 'ERROR',
    
    # CORS
    'CORS_ORIGINS': '*',
    
    # Server settings
    'HOST': 'localhost',
    'PORT': '5000'
}

def setup_test_environment():
    """Set up test environment variables"""
    for key, value in DEFAULT_TEST_ENV.items():
        if key not in os.environ:
            os.environ[key] = value

# ========================================
# TEST DISCOVERY CONFIGURATION
# ========================================

# Test module patterns
TEST_MODULE_PATTERNS = [
    'test_*_api.py',
    'test_*.py'
]

# Expected test modules for each API
API_TEST_MODULES = {
    'estudiantes': [
        'test_estudiantes_api',
        'test_estudiantes'  # Fallback for legacy
    ],
    'ayudantes': [
        'test_ayudantes_api',
        'test_ayudantes'    # Fallback for legacy
    ],
    'lector': [
        'test_lector_api',
        'test_lector'       # Fallback for legacy
    ]
}

# ========================================
# MOCK CONFIGURATION
# ========================================

# Common mock data for tests
MOCK_STUDENT_DATA = {
    'id': 1,
    'nombre': 'Juan Test',
    'apellido': 'Pérez Test',
    'email': 'juan.test@estudiante.com',
    'activo': 1,
    'TP': 'Ingeniería Informática'
}

MOCK_HELPER_DATA = {
    'id': 1,
    'nombre': 'María Test',
    'apellido': 'González Test',
    'email': 'maria.test@ayudante.com',
    'activo': 1
}

MOCK_QR_DATA_STUDENT = {
    'name': 'Juan Test',
    'surname': 'Pérez Test',
    'email': 'juan.test@estudiante.com',
    'tipoUsuario': 'ESTUDIANTE',
    'timestamp': 1703507400000,  # Fixed timestamp for predictable testing
    'status': 'VALID'
}

MOCK_QR_DATA_HELPER = {
    'name': 'María Test',
    'surname': 'González Test',
    'email': 'maria.test@ayudante.com',
    'tipoUsuario': 'AYUDANTE',
    'timestamp': 1703507400000,  # Fixed timestamp for predictable testing
    'status': 'VALID'
}

MOCK_REGISTRO_DATA = {
    'id': 1,
    'fecha': '2023-12-25',
    'hora': '10:30:00',
    'dia': 'lunes',
    'nombre': 'Juan Test',
    'apellido': 'Pérez Test',
    'email': 'juan.test@estudiante.com',
    'tipo': 'Entrada',
    'auto_generado': False
}

# ========================================
# DATABASE MOCK CONFIGURATION
# ========================================

# Mock database configuration
MOCK_DB_CONFIG = {
    'host': 'localhost',
    'user': 'test_user',
    'password': 'test_password',
    'database': 'test_database',
    'port': 3306,
    'charset': 'utf8mb4'
}

# Mock database responses
MOCK_DB_RESPONSES = {
    'student_found': MOCK_STUDENT_DATA,
    'student_not_found': None,
    'student_inactive': {**MOCK_STUDENT_DATA, 'activo': 0},
    'helper_found': MOCK_HELPER_DATA,
    'helper_not_found': None,
    'helper_inactive': {**MOCK_HELPER_DATA, 'activo': 0},
    'empty_result': [],
    'single_registro': [MOCK_REGISTRO_DATA],
    'multiple_registros': [MOCK_REGISTRO_DATA, {**MOCK_REGISTRO_DATA, 'id': 2, 'tipo': 'Salida'}]
}

# ========================================
# TEST RESULT CONFIGURATION
# ========================================

# Expected response structures
EXPECTED_SUCCESS_RESPONSE = {
    'required_fields': ['success', 'data', 'timestamp'],
    'success_value': True,
    'status_field': 'status'
}

EXPECTED_ERROR_RESPONSE = {
    'required_fields': ['success', 'error', 'timestamp'],
    'success_value': False,
    'error_field': 'error'
}

EXPECTED_QR_VALIDATION_SUCCESS = {
    'required_fields': ['success', 'tipo', 'usuario_tipo', 'message'],
    'success_value': True,
    'valid_tipos': ['Entrada', 'Salida'],
    'valid_user_tipos': ['ESTUDIANTE', 'AYUDANTE']
}

EXPECTED_QR_VALIDATION_ERROR = {
    'required_fields': ['success', 'error'],
    'success_value': False,
    'optional_fields': ['expired']
}

# ========================================
# UTILITY FUNCTIONS
# ========================================

def get_api_module_path(api_name):
    """Get the file system path for an API module"""
    path_mapping = {
        'estudiantes': ESTUDIANTES_PATH,
        'ayudantes': AYUDANTES_PATH,
        'lector': LECTOR_PATH
    }
    return path_mapping.get(api_name)

def get_test_modules_for_api(api_name):
    """Get the test modules that should exist for an API"""
    return API_TEST_MODULES.get(api_name, [])

def create_mock_db_connection():
    """Create a mock database connection for testing"""
    from unittest.mock import MagicMock
    
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    return mock_conn, mock_cursor

def validate_response_structure(response_data, expected_structure):
    """Validate that a response has the expected structure"""
    if not isinstance(response_data, dict):
        return False, "Response is not a dictionary"
    
    # Check required fields
    for field in expected_structure['required_fields']:
        if field not in response_data:
            return False, f"Missing required field: {field}"
    
    # Check success value if specified
    if 'success_value' in expected_structure:
        if response_data.get('success') != expected_structure['success_value']:
            return False, f"Expected success={expected_structure['success_value']}, got {response_data.get('success')}"
    
    return True, "Valid structure"

def setup_full_test_environment():
    """Set up complete test environment"""
    setup_test_paths()
    setup_test_environment()

# ========================================
# TEST UTILITIES
# ========================================

class TestEnvironment:
    """Context manager for test environment setup"""
    
    def __init__(self, api_name=None):
        self.api_name = api_name
        self.original_path = sys.path.copy()
        self.original_env = os.environ.copy()
    
    def __enter__(self):
        setup_full_test_environment()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original sys.path
        sys.path[:] = self.original_path
        
        # Restore original environment (remove test variables)
        for key in DEFAULT_TEST_ENV:
            if key in self.original_env:
                os.environ[key] = self.original_env[key]
            elif key in os.environ:
                del os.environ[key]

# ========================================
# INITIALIZATION
# ========================================

# Auto-setup when module is imported
setup_full_test_environment()

# Export commonly used items
__all__ = [
    'setup_test_paths',
    'setup_test_environment', 
    'setup_full_test_environment',
    'TestEnvironment',
    'MOCK_STUDENT_DATA',
    'MOCK_HELPER_DATA',
    'MOCK_QR_DATA_STUDENT',
    'MOCK_QR_DATA_HELPER',
    'MOCK_REGISTRO_DATA',
    'MOCK_DB_CONFIG',
    'MOCK_DB_RESPONSES',
    'EXPECTED_SUCCESS_RESPONSE',
    'EXPECTED_ERROR_RESPONSE',
    'EXPECTED_QR_VALIDATION_SUCCESS',
    'EXPECTED_QR_VALIDATION_ERROR',
    'get_api_module_path',
    'get_test_modules_for_api',
    'create_mock_db_connection',
    'validate_response_structure'
]
