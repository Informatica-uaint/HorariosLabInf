import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Alert, Dimensions, TouchableOpacity } from 'react-native';
import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import { Ionicons } from '@expo/vector-icons';

const { width, height } = Dimensions.get('window');

// Configuración de la API
const API_BASE_URL = 'https://api.acceso.informaticauaint.com/api/lector';

interface ScanResult {
  success: boolean;
  tipo?: 'Entrada' | 'Salida';
  usuario_tipo?: 'ESTUDIANTE' | 'AYUDANTE';
  nombre?: string;
  apellido?: string;
  email?: string;
  message?: string;
  error?: string;
  expired?: boolean;
}

export default function QRReaderScreen() {
  const [facing, setFacing] = useState<CameraType>('back');
  const [permission, requestPermission] = useCameraPermissions();
  const [isScanning, setIsScanning] = useState(true);
  const [lastScanTime, setLastScanTime] = useState(0);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const scanTimeoutRef = useRef<NodeJS.Timeout>();

  // Procesar código QR escaneado
  const handleQRScanned = async (data: string) => {
    const now = Date.now();

    // Evitar escaneos múltiples rápidos
    if (now - lastScanTime < 2000) return;

    setLastScanTime(now);
    setIsScanning(false);

    try {
      // Parsear datos del QR
      let qrData;
      try {
        qrData = JSON.parse(data);
      } catch {
        throw new Error('Formato de QR inválido');
      }

      console.log('QR Data:', qrData);

      // Enviar a la API
      const response = await fetch(`${API_BASE_URL}/validate-qr`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(qrData),
      });

      const result: ScanResult = await response.json();
      console.log('API Response:', result);

      setScanResult(result);

      // Auto-reactivar escáner después de 3 segundos
      scanTimeoutRef.current = setTimeout(() => {
        setScanResult(null);
        setIsScanning(true);
      }, 3000);

    } catch (error) {
      console.error('Error processing QR:', error);
      setScanResult({
        success: false,
        error: error instanceof Error ? error.message : 'Error desconocido'
      });

      // Auto-reactivar escáner después de 3 segundos en caso de error
      scanTimeoutRef.current = setTimeout(() => {
        setScanResult(null);
        setIsScanning(true);
      }, 3000);
    }
  };

  // Limpiar timeout al desmontar
  useEffect(() => {
    return () => {
      if (scanTimeoutRef.current) {
        clearTimeout(scanTimeoutRef.current);
      }
    };
  }, []);

  // Reactivar escáner manualmente
  const handleManualReactivate = () => {
    if (scanTimeoutRef.current) {
      clearTimeout(scanTimeoutRef.current);
    }
    setScanResult(null);
    setIsScanning(true);
  };

  // Pantalla principal del lector
  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Lector QR - Control de Acceso</Text>
        <View style={styles.statusIndicator}>
          <View style={[
            styles.statusDot,
            { backgroundColor: isScanning ? '#4CAF50' : '#FF9800' }
          ]} />
          <Text style={styles.statusText}>
            {isScanning ? 'Esperando QR...' : 'Procesando...'}
          </Text>
        </View>
      </View>

      {/* Resultado del escaneo */}
      {scanResult && (
        <View style={[
          styles.resultContainer,
          {
            backgroundColor: scanResult.success
              ? (scanResult.tipo === 'Entrada' ? '#E8F5E8' : '#E3F2FD')
              : '#FFEBEE'
          }
        ]}>
          <View style={styles.resultIcon}>
            {scanResult.success ? (
              <Ionicons
                name={scanResult.tipo === 'Entrada' ? 'enter' : 'exit'}
                size={60}
                color={scanResult.tipo === 'Entrada' ? '#4CAF50' : '#2196F3'}
              />
            ) : (
              <Ionicons name="close-circle" size={60} color="#F44336" />
            )}
          </View>

          <Text style={[
            styles.resultTitle,
            {
              color: scanResult.success
                ? (scanResult.tipo === 'Entrada' ? '#2E7D32' : '#1976D2')
                : '#C62828'
            }
          ]}>
            {scanResult.success
              ? `${scanResult.tipo?.toUpperCase()} REGISTRADA`
              : 'ERROR'
            }
          </Text>

          {scanResult.success && (
            <>
              <Text style={styles.resultName}>
                {scanResult.nombre} {scanResult.apellido}
              </Text>
              <Text style={styles.resultType}>
                {scanResult.usuario_tipo}
              </Text>
            </>
          )}

          {scanResult.error && (
            <Text style={styles.resultError}>{scanResult.error}</Text>
          )}

          <TouchableOpacity
            style={styles.reactivateButton}
            onPress={handleManualReactivate}
          >
            <Ionicons name="refresh" size={24} color="#FFF" />
            <Text style={styles.reactivateText}>Escanear Nuevo QR</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Cámara */}
      {isScanning && (
        <View style={styles.cameraContainer}>
          <CameraView
            style={styles.camera}
            facing={facing}
            onBarcodeScanned={({ data }) => handleQRScanned(data)}
            barcodeScannerSettings={{
              barcodeTypes: ['qr'],
            }}
          />

          {/* Overlay de escaneo */}
          <View style={styles.scanOverlay}>
            <View style={styles.scanFrame} />
            <Text style={styles.scanInstructions}>
              Apunte la cámara hacia el código QR
            </Text>
          </View>
        </View>
      )}

      {/* Botones de control */}
      <View style={styles.controls}>
        <TouchableOpacity
          style={styles.controlButton}
          onPress={() => setFacing(facing === 'back' ? 'front' : 'back')}
        >
          <Ionicons name="camera-reverse" size={28} color="#FFF" />
          <Text style={styles.controlText}>Cambiar Cámara</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  // Verificar permisos de cámara
  if (!permission) {
    return <View style={styles.container}><Text>Solicitando permisos de cámara...</Text></View>;
  }

  if (!permission.granted) {
    return (
      <View style={styles.permissionContainer}>
        <Ionicons name="camera-off" size={80} color="#666" />
        <Text style={styles.permissionTitle}>Permiso de Cámara Requerido</Text>
        <Text style={styles.permissionSubtitle}>
          Esta aplicación necesita acceso a la cámara para leer códigos QR
        </Text>
        <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
          <Text style={styles.permissionButtonText}>Conceder Permiso</Text>
        </TouchableOpacity>
      </View>
    );
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },

  // Permisos
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
    padding: 20,
  },
  permissionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 20,
    marginBottom: 10,
  },
  permissionSubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 30,
  },
  permissionButton: {
    backgroundColor: '#2196F3',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 8,
  },
  permissionButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
  },

  // Header
  header: {
    backgroundColor: '#1976D2',
    padding: 15,
    alignItems: 'center',
  },
  headerTitle: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  statusIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 8,
  },
  statusText: {
    color: '#FFF',
    fontSize: 14,
  },

  // Resultado
  resultContainer: {
    margin: 15,
    padding: 20,
    borderRadius: 10,
    alignItems: 'center',
  },
  resultIcon: {
    marginBottom: 10,
  },
  resultTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  resultName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 5,
  },
  resultType: {
    fontSize: 14,
    color: '#666',
    marginBottom: 15,
  },
  resultError: {
    fontSize: 16,
    color: '#C62828',
    textAlign: 'center',
    marginBottom: 15,
  },
  reactivateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2196F3',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 5,
    gap: 8,
  },
  reactivateText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },

  // Cámara
  cameraContainer: {
    flex: 1,
    margin: 15,
    borderRadius: 10,
    overflow: 'hidden',
  },
  camera: {
    flex: 1,
  },
  scanOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanFrame: {
    width: 200,
    height: 200,
    borderWidth: 3,
    borderColor: '#4CAF50',
    borderRadius: 10,
    backgroundColor: 'transparent',
  },
  scanInstructions: {
    color: '#FFF',
    fontSize: 16,
    marginTop: 20,
    textAlign: 'center',
    backgroundColor: 'rgba(0,0,0,0.7)',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 5,
  },

  // Controles
  controls: {
    flexDirection: 'row',
    justifyContent: 'center',
    padding: 15,
    backgroundColor: '#1976D2',
  },
  controlButton: {
    backgroundColor: '#2196F3',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderRadius: 8,
    alignItems: 'center',
    minWidth: 120,
  },
  controlText: {
    color: '#FFF',
    fontSize: 12,
    marginTop: 5,
    fontWeight: '600',
  },
});