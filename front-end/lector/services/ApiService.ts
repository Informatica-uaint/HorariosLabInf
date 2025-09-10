import { Config } from '@/constants/Config';
import { API_ENDPOINTS } from '@/constants/ApiConfig';

export interface QRData {
  name: string;
  surname: string;
  email: string;
  tipoUsuario: 'ESTUDIANTE' | 'AYUDANTE';
  timestamp: number;
  expired?: boolean;
  status?: string;
}

export interface ScanResult {
  success: boolean;
  tipo?: 'Entrada' | 'Salida';
  usuario_tipo?: 'ESTUDIANTE' | 'AYUDANTE';
  nombre?: string;
  apellido?: string;
  email?: string;
  fecha?: string;
  hora?: string;
  message?: string;
  error?: string;
  expired?: boolean;
}

export interface Stats {
  success: boolean;
  date: string;
  students: {
    entries: number;
    exits: number;
  };
  helpers: {
    entries: number;
    exits: number;
  };
  error?: string;
}

export interface Record {
  tipo_usuario: 'ESTUDIANTE' | 'AYUDANTE';
  nombre: string;
  apellido: string;
  email: string;
  fecha: string;
  hora: string;
  tipo: 'Entrada' | 'Salida';
}

export interface RecordsResponse {
  success: boolean;
  records: Record[];
  error?: string;
}

class ApiService {
  private baseURL: string;
  private timeout: number;

  constructor() {
    this.baseURL = API_ENDPOINTS.QR.VALIDATE.replace('/validate-qr', ''); // Base URL sin endpoint específico
    this.timeout = Config.NETWORK.REQUEST_TIMEOUT;
  }

  /**
   * Realizar una petición HTTP con timeout y reintentos
   */
  private async fetchWithRetry(
    url: string,
    options: RequestInit = {},
    retries: number = Config.NETWORK.MAX_RETRIES
  ): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return response;
    } catch (error) {
      clearTimeout(timeoutId);

      if (retries > 0 && error instanceof Error) {
        if (Config.LOGGING.ENABLE_CONSOLE_LOGS) {
          console.warn(`Request failed, retrying... (${retries} attempts left)`, error.message);
        }

        await new Promise(resolve => setTimeout(resolve, Config.NETWORK.RETRY_INTERVAL));
        return this.fetchWithRetry(url, options, retries - 1);
      }

      throw error;
    }
  }

  /**
   * Validar código QR y registrar acceso
   */
  async validateQR(qrData: QRData): Promise<ScanResult> {
    try {
      if (Config.LOGGING.ENABLE_CONSOLE_LOGS) {
        console.log('Validating QR:', qrData);
      }

      const response = await this.fetchWithRetry(API_ENDPOINTS.QR.VALIDATE, {
        method: 'POST',
        body: JSON.stringify(qrData),
      });

      const result = await response.json();

      if (Config.LOGGING.ENABLE_CONSOLE_LOGS) {
        console.log('QR validation result:', result);
      }

      return result;
    } catch (error) {
      console.error('Error validating QR:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Error de conexión'
      };
    }
  }

  /**
   * Obtener estadísticas del día
   */
  async getStats(): Promise<Stats> {
    try {
      const response = await this.fetchWithRetry(API_ENDPOINTS.QR.STATS);
      const result = await response.json();

      if (Config.LOGGING.ENABLE_CONSOLE_LOGS) {
        console.log('Stats result:', result);
      }

      return result;
    } catch (error) {
      console.error('Error fetching stats:', error);
      return {
        success: false,
        date: new Date().toISOString().split('T')[0],
        students: { entries: 0, exits: 0 },
        helpers: { entries: 0, exits: 0 },
        error: error instanceof Error ? error.message : 'Error de conexión'
      };
    }
  }

  /**
   * Obtener últimos registros
   */
  async getLastRecords(limit: number = 20): Promise<RecordsResponse> {
    try {
      const response = await this.fetchWithRetry(`${API_ENDPOINTS.QR.RECORDS}?limit=${limit}`);
      const result = await response.json();

      if (Config.LOGGING.ENABLE_CONSOLE_LOGS) {
        console.log('Records result:', result);
      }

      return result;
    } catch (error) {
      console.error('Error fetching records:', error);
      return {
        success: false,
        records: [],
        error: error instanceof Error ? error.message : 'Error de conexión'
      };
    }
  }

  /**
   * Verificar si un estudiante existe
   */
  async verifyStudent(email: string): Promise<any> {
    try {
      const response = await this.fetchWithRetry(API_ENDPOINTS.QR.VERIFY_STUDENT, {
        method: 'POST',
        body: JSON.stringify({ email }),
      });

      return await response.json();
    } catch (error) {
      console.error('Error verifying student:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Error de conexión'
      };
    }
  }

  /**
   * Verificar si un ayudante existe
   */
  async verifyHelper(email: string): Promise<any> {
    try {
      const response = await this.fetchWithRetry(API_ENDPOINTS.QR.VERIFY_HELPER, {
        method: 'POST',
        body: JSON.stringify({ email }),
      });

      return await response.json();
    } catch (error) {
      console.error('Error verifying helper:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Error de conexión'
      };
    }
  }

  /**
   * Verificar estado de la API
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.fetchWithRetry(API_ENDPOINTS.HEALTH);
      const result = await response.json();
      return result.status === 'ok';
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }
}

// Exportar instancia singleton
export const apiService = new ApiService();
export default ApiService;