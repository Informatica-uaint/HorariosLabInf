// Configuración de la aplicación
export const Config = {
  // URL base de la API unificada
  API_BASE_URL: 'https://acceso.informaticauaint.com/api/qr',

  // Clave de acceso para dispositivos autorizados
  // PIN numérico de 4 dígitos - Cambia por tu PIN deseado
  ACCESS_KEY: '1234',

  // Configuración del escáner QR
  QR_SCANNER: {
    // Tiempo mínimo entre escaneos (ms)
    MIN_SCAN_INTERVAL: 2000,

    // Tiempo de auto-reactivación después de resultado (ms)
    AUTO_REACTIVATE_DELAY: 3000,

    // Tipos de códigos de barras a escanear
    BARCODE_TYPES: ['qr'],
  },

  // Configuración de la interfaz
  UI: {
    // Tamaño de la pantalla (para optimización)
    SMALL_SCREEN: true,

    // Colores del tema
    COLORS: {
      PRIMARY: '#1976D2',
      SUCCESS: '#4CAF50',
      WARNING: '#FF9800',
      ERROR: '#F44336',
      BACKGROUND: '#F5F5F5',
      WHITE: '#FFFFFF',
      TEXT: '#333333',
      TEXT_LIGHT: '#666666',
    },

    // Configuración de botones para pantalla pequeña
    BUTTON_SIZE: {
      LARGE: {
        width: 120,
        height: 60,
        fontSize: 14,
      },
      MEDIUM: {
        width: 100,
        height: 50,
        fontSize: 12,
      },
    },
  },

  // Configuración de red
  NETWORK: {
    // Timeout para requests (ms)
    REQUEST_TIMEOUT: 10000,

    // Reintentos automáticos
    MAX_RETRIES: 3,

    // Intervalo de reintento (ms)
    RETRY_INTERVAL: 1000,
  },

  // Configuración de almacenamiento local
  STORAGE: {
    // Claves para localStorage
    KEYS: {
      ACCESS_KEY: 'lector_access_key',
      LAST_SCAN: 'last_scan_time',
      DEVICE_ID: 'device_id',
    },
  },

  // Configuración de logging
  LOGGING: {
    // Habilitar logs en consola
    ENABLE_CONSOLE_LOGS: true,

    // Nivel de log
    LOG_LEVEL: 'info',
  },
};

// Función para generar ID único del dispositivo
export const generateDeviceId = (): string => {
  const stored = localStorage.getItem(Config.STORAGE.KEYS.DEVICE_ID);
  if (stored) return stored;

  const deviceId = `lector-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  localStorage.setItem(Config.STORAGE.KEYS.DEVICE_ID, deviceId);
  return deviceId;
};

// Función para validar configuración de red
export const validateNetworkConfig = (): boolean => {
  try {
    new URL(Config.API_BASE_URL);
    return true;
  } catch {
    return false;
  }
};

export default Config;