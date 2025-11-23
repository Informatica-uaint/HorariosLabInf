// API Configuration for HorariosLabInf
// This file centralizes all API endpoint configurations

// Get the API base URL from environment variable or use origin-based fallback
const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_URL ||
  (typeof window !== 'undefined'
    ? `${window.location.origin}/api`
    : 'https://api.acceso.informaticauaint.com/api');

export const API_CONFIG = {
  BASE_URL: API_BASE_URL,
  TIMEOUT: 10000, // 10 seconds timeout
  HEADERS: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
};

export const API_ENDPOINTS = {
  // Estudiantes endpoints
  ESTUDIANTES: {
    BASE: `${API_BASE_URL}/estudiantes`,
    VALIDATE_QR: `${API_BASE_URL}/estudiantes/validate_qr`,
    LIST: `${API_BASE_URL}/estudiantes/estudiantes`,
    PRESENT: `${API_BASE_URL}/estudiantes/estudiantes_presentes`,
    RECORDS: `${API_BASE_URL}/estudiantes/registros_estudiantes`,
    REGISTROS: `${API_BASE_URL}/estudiantes/registros_estudiantes`
  },

  // Ayudantes endpoints
  AYUDANTES: {
    BASE: `${API_BASE_URL}/ayudantes`,
    VALIDATE_QR: `${API_BASE_URL}/ayudantes/validate_qr`,
    LIST: `${API_BASE_URL}/ayudantes/ayudantes`,
    PRESENT: `${API_BASE_URL}/ayudantes_presentes`,
    RECORDS: `${API_BASE_URL}/ayudantes/registros`,
    REGISTROS: `${API_BASE_URL}/registros`,
    HORAS: `${API_BASE_URL}/horas_acumuladas`,
    CUMPLIMIENTO: `${API_BASE_URL}/cumplimiento`
  },

  // Authentication endpoints
  AUTH: {
    BASE: `${API_BASE_URL}/auth`,
    LOGIN: `${API_BASE_URL}/auth/login`,
    VALIDATE: `${API_BASE_URL}/auth/validate`,
    REFRESH: `${API_BASE_URL}/auth/refresh`
  },

  // QR code endpoints
  QR: {
    BASE: `${API_BASE_URL}/qr`,
    VALIDATE: `${API_BASE_URL}/qr/validate`
  },

  // Lector QR dinámico
  READER: {
    VALIDATE: `${API_BASE_URL}/lector/validar`
  },

  // Health check
  HEALTH: `${API_BASE_URL}/health`
};

// Utility function to build API URLs
export const buildApiUrl = (endpoint: string, params?: Record<string, string | number>): string => {
  let url = endpoint;

  if (params) {
    const queryString = Object.entries(params)
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
      .join('&');

    url += `?${queryString}`;
  }

  return url;
};

// Common fetch options
export const createFetchOptions = (method: string = 'GET', body?: any): RequestInit => {
  const options: RequestInit = {
    method,
    headers: API_CONFIG.HEADERS,
    timeout: API_CONFIG.TIMEOUT
  };

  if (body && method !== 'GET') {
    options.body = JSON.stringify(body);
  }

  return options;
};

// API client helper function
export const apiRequest = async (url: string, options?: RequestInit) => {
  try {
    const response = await fetch(url, {
      ...createFetchOptions(),
      ...options
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};
