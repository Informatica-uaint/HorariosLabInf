import React, { useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, ActivityIndicator, Alert, Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { StatusBar } from 'expo-status-bar';
import { API_ENDPOINTS } from '../../../constants/ApiConfig';

// Conditional imports for native only
let BarCodeScanner: any;
let BarCodeScannerResult: any;
if (Platform.OS !== 'web') {
  const barcodeModule = require('expo-barcode-scanner');
  BarCodeScanner = barcodeModule.BarCodeScanner;
}

type AccessResult = {
  success?: boolean;
  message?: string;
  error?: string;
  tipo?: string;
  estado?: string;
  station_id?: string;
};

const STORAGE_KEY = 'scanner_user_estudiante';
const TOKEN_STORAGE_KEY = 'reader_token_session';
const TOKEN_TTL_MS = 55000;

const extractReaderToken = (raw: string) => {
  if (!raw) return '';
  try {
    const url = new URL(raw.trim());
    const fromQuery = url.searchParams.get('readerToken');
    if (fromQuery) return fromQuery;
  } catch {
    // Not a URL, continue fallback
  }
  const match = raw.match(/readerToken=([^&\s]+)/i);
  if (match?.[1]) {
    try {
      return decodeURIComponent(match[1]);
    } catch {
      return match[1];
    }
  }
  return raw.trim();
};

const saveSessionToken = (token: string) => {
  if (typeof window === 'undefined') return;
  try {
    sessionStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify({ token, savedAt: Date.now() }));
  } catch {
    // ignore
  }
};

const getSessionToken = () => {
  if (typeof window === 'undefined') return '';
  try {
    const raw = sessionStorage.getItem(TOKEN_STORAGE_KEY);
    if (!raw) return '';
    const parsed = JSON.parse(raw);
    if (!parsed?.token) return '';
    if (Date.now() - (parsed.savedAt || 0) > TOKEN_TTL_MS) {
      sessionStorage.removeItem(TOKEN_STORAGE_KEY);
      return '';
    }
    return parsed.token as string;
  } catch {
    return '';
  }
};

export default function EstudiantesScan() {
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [scanning, setScanning] = useState(false);
  const [name, setName] = useState('');
  const [surname, setSurname] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastResult, setLastResult] = useState<AccessResult | null>(null);
  const [manualToken, setManualToken] = useState('');
  const [step, setStep] = useState<'form' | 'scan'>('form');
  const isWeb = Platform.OS === 'web';
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const scanInterval = useRef<NodeJS.Timeout | null>(null);
  const [webError, setWebError] = useState('');
  const readerRef = useRef<any>(null);
  const autoSubmitted = useRef(false);
  const [pendingToken, setPendingToken] = useState('');

  useEffect(() => {
    if (!isWeb) {
      requestPermission();
    } else {
      setHasPermission(true);
    }
    hydrateUser();
    const initialToken = extractReaderToken(typeof window !== 'undefined' ? window.location.href : '');
    if (initialToken) {
      saveSessionToken(initialToken);
      setPendingToken(initialToken);
      setManualToken(initialToken);
    } else {
      const stored = getSessionToken();
      if (stored) {
        setPendingToken(stored);
        setManualToken(stored);
      }
    }
    return () => stopWebScanner();
  }, [isWeb]);

  useEffect(() => {
    if (isWeb && step === 'scan') {
      startWebScanner();
      const stored = getSessionToken();
      if (stored && !autoSubmitted.current) {
        autoSubmitted.current = true;
        submitAccess(stored, { fromStored: true });
      }
    } else {
      stopWebScanner();
    }
  }, [isWeb, step]);

  const requestPermission = async () => {
    const { status } = await BarCodeScanner.requestPermissionsAsync();
    setHasPermission(status === 'granted');
  };

  const hydrateUser = async () => {
    const stored = await AsyncStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      setName(parsed.name || '');
      setSurname(parsed.surname || '');
      setEmail(parsed.email || '');
    }
  };

  const persistUser = async () => {
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify({ name, surname, email }));
  };

  const handleBarCodeScanned = async ({ data }: BarCodeScannerResult) => {
    setScanning(false);
    if (!data) return;
    await persistUser();
    submitAccess(data);
  };

  const resolveToken = (raw: string) => {
    const extracted = extractReaderToken(raw);
    if (extracted) {
      saveSessionToken(extracted);
      return extracted;
    }
    const stored = getSessionToken();
    if (stored) return stored;
    return '';
  };

  const submitAccess = async (token: string, opts?: { fromStored?: boolean }) => {
    const finalToken = resolveToken(token || pendingToken);
    if (!name || !surname || !email) {
      Alert.alert('Datos incompletos', 'Completa nombre, apellido y correo antes de escanear.');
      return;
    }

    if (!finalToken) {
      Alert.alert('QR vacío', 'No se recibió un token de QR.');
      return;
    }

    setLoading(true);
    setLastResult(null);
    try {
      const response = await fetch(API_ENDPOINTS.READER.VALIDATE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: finalToken,
          nombre: name.trim(),
          apellido: surname.trim(),
          email: email.trim()
        })
      });

      const result = await response.json();
      setLastResult(result);
      if (!response.ok) {
        const message = result?.error || 'No se pudo registrar el acceso';
        Alert.alert('Acceso denegado', message);
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'No se pudo contactar al servidor');
    } finally {
      setLoading(false);
      setScanning(true);
      if (!opts?.fromStored) {
        autoSubmitted.current = false;
      }
    }
  };

  const goToScan = async () => {
    if (!name || !surname || !email) {
      Alert.alert('Datos incompletos', 'Completa nombre, apellido y correo.');
      return;
    }
    await persistUser();
    setStep('scan');
    if (!isWeb) {
      setScanning(true);
    }
  };

  const backToForm = () => {
    stopWebScanner();
    setScanning(false);
    setStep('form');
  };

  const startWebScanner = async () => {
    if (!isWeb || typeof window === 'undefined') return;
    // @ts-ignore
    const BarcodeDetector = (window as any).BarcodeDetector;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(() => {});
      }

      if (BarcodeDetector) {
        const detector = new BarcodeDetector({ formats: ['qr_code'] });
        scanInterval.current = setInterval(async () => {
          if (!videoRef.current) return;
          try {
            const codes = await detector.detect(videoRef.current);
            if (codes && codes.length > 0) {
              const value = codes[0].rawValue;
              stopWebScanner();
              submitAccess(value);
            }
          } catch {
            // silencioso
          }
        }, 400);
      } else {
        // Fallback con ZXing para navegadores sin BarcodeDetector
        const { BrowserMultiFormatReader, NotFoundException } = await import('@zxing/browser');
        const reader = new BrowserMultiFormatReader();
        readerRef.current = reader;
        reader.decodeFromVideoDevice(
          undefined,
          videoRef.current as any,
          (result, err) => {
            if (result?.getText()) {
              stopWebScanner();
              submitAccess(result.getText());
            }
            if (err && !(err instanceof NotFoundException)) {
              // otros errores se ignoran en bucle
            }
          }
        );
      }
    } catch (err: any) {
      setWebError(err?.message || 'No se pudo acceder a la cámara');
    }
  };

  const stopWebScanner = () => {
    if (scanInterval.current) {
      clearInterval(scanInterval.current);
      scanInterval.current = null;
    }
    if (readerRef.current) {
      try {
        readerRef.current.reset();
      } catch (e) {
        // ignore
      }
      readerRef.current = null;
    }
    if (videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
      tracks.forEach((t) => t.stop());
    }
  };

  if (hasPermission === null) {
    return (
      <View style={styles.centered}>
        <Text style={styles.muted}>Solicitando permiso de cámara...</Text>
      </View>
    );
  }

  if (hasPermission === false) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>Permiso de cámara denegado.</Text>
        <Text style={styles.muted}>Habilita la cámara para escanear el QR del lector.</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      <Text style={styles.title}>
        {step === 'form' ? 'Ingresa tus datos' : 'Escanea el QR del lector'}
      </Text>
      <Text style={styles.subtitle}>
        {step === 'form'
          ? 'Portal Estudiantes: valida tus credenciales con el código mostrado por el lector.'
          : 'Apunta la cámara al QR. Los datos ingresados se guardan para próximos accesos.'}
      </Text>

      {step === 'form' ? (
        <View style={styles.form}>
          <TextInput
            placeholder="Nombre"
            style={styles.input}
            value={name}
            onChangeText={setName}
            autoCapitalize="words"
          />
          <TextInput
            placeholder="Apellido"
            style={styles.input}
            value={surname}
            onChangeText={setSurname}
            autoCapitalize="words"
          />
          <TextInput
            placeholder="Correo institucional"
            style={styles.input}
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
          />
          <TouchableOpacity style={styles.button} onPress={goToScan}>
            <Text style={styles.buttonText}>Continuar</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <>
          {isWeb ? (
            <View style={styles.scannerContainerWeb}>
              {webError ? (
                <View style={styles.manualBox}>
                  <Text style={styles.muted}>{webError}</Text>
                  <TextInput
                    placeholder="Pega el token del QR"
                    style={styles.input}
                    value={manualToken}
                    onChangeText={setManualToken}
                    autoCapitalize="none"
                    autoCorrect={false}
                  />
                  <TouchableOpacity style={styles.button} onPress={() => submitAccess(manualToken)}>
                    <Text style={styles.buttonText}>Validar token</Text>
                  </TouchableOpacity>
                </View>
              ) : (
                <video
                  ref={videoRef}
                  style={styles.video}
                  muted
                  playsInline
                  autoPlay
                />
              )}
            </View>
          ) : (
            <View style={styles.scannerContainer}>
              {scanning ? (
                <BarCodeScanner
                  onBarCodeScanned={handleBarCodeScanned}
                  style={StyleSheet.absoluteFillObject}
                />
              ) : (
                <View style={styles.placeholder}>
                  <Text style={styles.muted}>Pulsa "Continuar" para escanear</Text>
                </View>
              )}
            </View>
          )}

          <TouchableOpacity style={styles.secondaryButton} onPress={backToForm}>
            <Text style={styles.buttonText}>Volver a datos</Text>
          </TouchableOpacity>
        </>
      )}

      {loading && (
        <View style={styles.statusBox}>
          <ActivityIndicator color="#fff" />
          <Text style={styles.statusText}>Validando acceso...</Text>
        </View>
      )}

      {lastResult && (
        <View style={[styles.statusBox, lastResult.success ? styles.success : styles.error]}>
          <Text style={styles.statusTitle}>
            {lastResult.success ? `Acceso ${lastResult.tipo || 'registrado'}` : 'Acceso denegado'}
          </Text>
          <Text style={styles.statusText}>{lastResult.message || lastResult.error}</Text>
          {lastResult.station_id && (
            <Text style={styles.statusText}>Estación: {lastResult.station_id}</Text>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
    padding: 20,
    gap: 12
  },
  title: {
    color: '#e2e8f0',
    fontSize: 24,
    fontWeight: '700'
  },
  subtitle: {
    color: '#94a3b8',
    fontSize: 14
  },
  form: {
    gap: 10
  },
  input: {
    backgroundColor: '#1e293b',
    color: '#e2e8f0',
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#334155'
  },
  button: {
    marginTop: 4,
    backgroundColor: '#2563eb',
    padding: 14,
    borderRadius: 10,
    alignItems: 'center'
  },
  secondaryButton: {
    marginTop: 12,
    backgroundColor: '#0f172a',
    padding: 12,
    borderRadius: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155'
  },
  buttonText: {
    color: '#e2e8f0',
    fontWeight: '600'
  },
  manualBox: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#334155',
    gap: 8
  },
  scannerContainer: {
    flex: 1,
    borderRadius: 14,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#334155',
    backgroundColor: '#1e293b'
  },
  scannerContainerWeb: {
    flex: 1,
    borderRadius: 14,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#334155',
    backgroundColor: '#1e293b',
    alignItems: 'center',
    justifyContent: 'center'
  },
  placeholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center'
  },
  video: {
    width: '100%',
    height: '100%',
    objectFit: 'cover'
  },
  statusBox: {
    backgroundColor: '#1e293b',
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#334155',
    gap: 4
  },
  statusText: {
    color: '#cbd5e1'
  },
  statusTitle: {
    color: '#e2e8f0',
    fontWeight: '700',
    fontSize: 16
  },
  success: {
    borderColor: '#22c55e'
  },
  error: {
    borderColor: '#f87171'
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0f172a',
    padding: 20,
    gap: 10
  },
  muted: {
    color: '#94a3b8'
  },
  errorText: {
    color: '#fca5a5',
    fontSize: 16,
    fontWeight: '600'
  }
});
