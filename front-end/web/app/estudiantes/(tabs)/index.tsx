import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, ActivityIndicator, Alert, Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { BarCodeScanner, BarCodeScannerResult } from 'expo-barcode-scanner';
import { StatusBar } from 'expo-status-bar';
import { API_ENDPOINTS } from '../../../constants/ApiConfig';

type AccessResult = {
  success?: boolean;
  message?: string;
  error?: string;
  tipo?: string;
  estado?: string;
  station_id?: string;
};

const STORAGE_KEY = 'scanner_user_estudiante';

export default function EstudiantesScan() {
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [scanning, setScanning] = useState(false);
  const [name, setName] = useState('');
  const [surname, setSurname] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastResult, setLastResult] = useState<AccessResult | null>(null);
  const [manualToken, setManualToken] = useState('');
  const isWeb = Platform.OS === 'web';

  useEffect(() => {
    if (!isWeb) {
      requestPermission();
    } else {
      setHasPermission(true);
    }
    hydrateUser();
  }, [isWeb]);

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

  const submitAccess = async (token: string) => {
    if (!name || !surname || !email) {
      Alert.alert('Datos incompletos', 'Completa nombre, apellido y correo antes de escanear.');
      return;
    }

    setLoading(true);
    setLastResult(null);
    try {
      const response = await fetch(API_ENDPOINTS.READER.VALIDATE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
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
      <Text style={styles.title}>Escanea o ingresa el QR del lector</Text>
      <Text style={styles.subtitle}>Portal Estudiantes: valida tus credenciales con el código mostrado por el lector.</Text>

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
        {!isWeb && (
          <TouchableOpacity style={styles.button} onPress={() => setScanning(true)}>
            <Text style={styles.buttonText}>Abrir cámara</Text>
          </TouchableOpacity>
        )}
      </View>

      {isWeb ? (
        <View style={styles.manualBox}>
          <Text style={styles.muted}>Componente de cámara no soportado en web. Pega el token del QR:</Text>
          <TextInput
            placeholder="Token del QR"
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
        <View style={styles.scannerContainer}>
          {scanning ? (
            <BarCodeScanner
              onBarCodeScanned={handleBarCodeScanned}
              style={StyleSheet.absoluteFillObject}
            />
          ) : (
            <View style={styles.placeholder}>
              <Text style={styles.muted}>Pulsa "Abrir cámara" para escanear</Text>
            </View>
          )}
        </View>
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
  placeholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center'
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
