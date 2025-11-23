// app/ayudantes/(tabs)/estudiantes.tsx
import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, FlatList, Platform, RefreshControl, Image, ActivityIndicator, TouchableOpacity, Alert, Modal } from 'react-native';

import { API_ENDPOINTS } from '../../../constants/ApiConfig';

export default function EstudiantesScreen() {
  const [estudiantes, setEstudiantes] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [markingExit, setMarkingExit] = useState(null); // Email del estudiante en proceso de salida

  const loadEstudiantes = () => {
    setRefreshing(true);
    setLoading(true);
    setError(null);

    const endpoint = API_ENDPOINTS.ESTUDIANTES.PRESENT;
    console.log("Cargando estudiantes desde:", endpoint);

    fetch(endpoint)
      .then(res => {
        if (!res.ok) {
          throw new Error(`Error ${res.status}: ${res.statusText || 'Error del servidor'}`);
        }
        return res.json();
      })
      .then(data => {
        console.log("Datos de estudiantes recibidos:", data);

        // Sanitizar y validar los datos recibidos
        const sanitizedData = Array.isArray(data) ? data.map(estudiante => ({
          id: estudiante.id || `eid-${Math.random().toString(36).substring(2, 9)}`,
          nombre: estudiante.nombre || 'Sin nombre',
          apellido: estudiante.apellido || 'Sin apellido',
          email: estudiante.email || 'sin-email@example.com',
          ultima_entrada: estudiante.ultima_entrada || '--:--',
          foto_url: estudiante.foto_url || null,
          estado: 'dentro' // Todos los estudiantes en esta lista están dentro
        })) : [];

        setEstudiantes(sanitizedData);
        setLastUpdated(new Date());
        setRefreshing(false);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error al cargar estudiantes presentes:', err);
        setError(`No se pudieron cargar los estudiantes: ${err.message}`);
        setRefreshing(false);
        setLoading(false);
        setEstudiantes([]);
      });
  };

  useEffect(() => {
    loadEstudiantes();
    const interval = setInterval(loadEstudiantes, 120000); // Actualizar cada 2 minutos
    return () => clearInterval(interval);
  }, []);

  const onRefresh = () => {
    loadEstudiantes();
  };

  const getInitials = (nombre, apellido) => {
    const nombreInit = nombre && nombre.charAt(0) ? nombre.charAt(0) : '';
    const apellidoInit = apellido && apellido.charAt(0) ? apellido.charAt(0) : '';
    return (nombreInit + apellidoInit).toUpperCase();
  };

  const formatEntryTime = (timeString) => {
    if (!timeString || timeString === '--:--') {
      return 'Hora no disponible';
    }

    try {
      if (timeString.includes('T')) {
        const date = new Date(timeString);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      }
      return timeString;
    } catch (e) {
      console.warn('Error formatting time:', e);
      return timeString;
    }
  };

  const handleMarcarSalida = (estudiante) => {
    if (Platform.OS === 'web') {
      // En web usar confirm nativo
      const confirmed = window.confirm(
        `¿Marcar salida de ${estudiante.nombre} ${estudiante.apellido}?`
      );
      if (confirmed) {
        marcarSalida(estudiante);
      }
    } else {
      // En móvil usar Alert de React Native
      Alert.alert(
        'Confirmar salida',
        `¿Marcar salida de ${estudiante.nombre} ${estudiante.apellido}?`,
        [
          { text: 'Cancelar', style: 'cancel' },
          { text: 'Confirmar', onPress: () => marcarSalida(estudiante) }
        ]
      );
    }
  };

  const marcarSalida = (estudiante) => {
    setMarkingExit(estudiante.email);

    const endpoint = API_ENDPOINTS.ESTUDIANTES.REGISTROS;
    const payload = {
      nombre: estudiante.nombre,
      apellido: estudiante.apellido,
      email: estudiante.email
    };

    console.log('Marcando salida para:', payload);

    fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    })
      .then(res => {
        if (!res.ok) {
          return res.json().then(err => {
            throw new Error(err.error || 'Error al marcar salida');
          });
        }
        return res.json();
      })
      .then(data => {
        console.log('Salida marcada exitosamente:', data);

        // Mostrar mensaje de éxito
        if (Platform.OS === 'web') {
          alert(`Salida registrada para ${estudiante.nombre} ${estudiante.apellido}`);
        } else {
          Alert.alert('Éxito', `Salida registrada para ${estudiante.nombre} ${estudiante.apellido}`);
        }

        // Recargar la lista
        loadEstudiantes();
      })
      .catch(err => {
        console.error('Error al marcar salida:', err);

        if (Platform.OS === 'web') {
          alert(`Error: ${err.message}`);
        } else {
          Alert.alert('Error', `No se pudo marcar la salida: ${err.message}`);
        }
      })
      .finally(() => {
        setMarkingExit(null);
      });
  };

  // Mostrar indicador de carga
  if (loading && !refreshing) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#0066CC" />
        <Text style={styles.loadingText}>Cargando estudiantes presentes...</Text>
      </View>
    );
  }

  // Mostrar mensaje de error
  if (error) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={loadEstudiantes}>
          <Text style={styles.retryButtonText}>Reintentar</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Estudiantes en el laboratorio</Text>

      {estudiantes.length === 0 && !refreshing ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>No hay estudiantes en el laboratorio actualmente</Text>
        </View>
      ) : (
        <FlatList
          data={estudiantes}
          keyExtractor={(item, index) => item.email || `item-${index}`}
          numColumns={2}
          columnWrapperStyle={styles.estudiantesRow}
          renderItem={({ item }) => (
            <View style={styles.estudianteCard}>
              <View style={styles.avatarContainer}>
                <View style={styles.avatarFallback}>
                  <Text style={styles.avatarInitials}>
                    {getInitials(item.nombre, item.apellido)}
                  </Text>
                </View>
                {item.foto_url ? (
                  <Image
                    source={{ uri: item.foto_url }}
                    style={styles.avatarImage}
                    onError={(e) => console.log('Error loading image:', e.nativeEvent.error)}
                  />
                ) : null}
              </View>
              <Text style={styles.estudianteNombre}>{item.nombre || 'Sin nombre'}</Text>
              <Text style={styles.estudianteApellido}>{item.apellido || 'Sin apellido'}</Text>
              <View style={styles.entradaContainer}>
                <Text style={styles.estudianteEntrada}>
                  Entrada: {formatEntryTime(item.ultima_entrada)}
                </Text>
                <View style={styles.estadoBadge}>
                  <Text style={styles.estadoText}>Presente</Text>
                </View>
              </View>

              {/* Botón de marcar salida */}
              <TouchableOpacity
                style={[
                  styles.salidaButton,
                  markingExit === item.email && styles.salidaButtonDisabled
                ]}
                onPress={() => handleMarcarSalida(item)}
                disabled={markingExit === item.email}
              >
                {markingExit === item.email ? (
                  <ActivityIndicator size="small" color="white" />
                ) : (
                  <Text style={styles.salidaButtonText}>Marcar Salida</Text>
                )}
              </TouchableOpacity>
            </View>
          )}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            refreshing ? null : (
              <View style={styles.emptyContainer}>
                <Text style={styles.emptyText}>No hay estudiantes en el laboratorio actualmente</Text>
              </View>
            )
          }
        />
      )}

      <Text style={styles.lastUpdate}>
        Última actualización: {lastUpdated.toLocaleTimeString()}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  errorText: {
    fontSize: 16,
    color: '#d32f2f',
    textAlign: 'center',
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#0066CC',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 5,
  },
  retryButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
  estudiantesRow: {
    justifyContent: 'space-between',
    marginBottom: 15,
  },
  estudianteCard: {
    width: '48%',
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 15,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
    marginBottom: 15,
  },
  avatarContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#f0f0f0',
    marginBottom: 10,
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
    position: 'relative',
  },
  avatarImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
    position: 'absolute',
    top: 0,
    left: 0,
    zIndex: 2,
  },
  avatarFallback: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#1890ff',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1,
  },
  avatarInitials: {
    color: 'white',
    fontSize: 40,
    fontWeight: 'bold',
  },
  estudianteNombre: {
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  estudianteApellido: {
    fontSize: 16,
    fontWeight: '500',
    textAlign: 'center',
  },
  entradaContainer: {
    marginTop: 5,
    alignItems: 'center',
  },
  estudianteEntrada: {
    fontSize: 12,
    color: '#666',
    marginBottom: 5,
  },
  estadoBadge: {
    backgroundColor: '#27ae60',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    marginBottom: 10,
  },
  estadoText: {
    color: 'white',
    fontSize: 10,
    fontWeight: 'bold',
  },
  salidaButton: {
    backgroundColor: '#e74c3c',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 5,
    marginTop: 5,
    minWidth: 120,
    alignItems: 'center',
  },
  salidaButtonDisabled: {
    backgroundColor: '#95a5a6',
  },
  salidaButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
    textAlign: 'center',
  },
  lastUpdate: {
    textAlign: 'center',
    fontSize: 12,
    color: '#999',
    marginTop: 10,
  },
});
