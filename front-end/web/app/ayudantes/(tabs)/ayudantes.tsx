// app/ayudantes.tsx
import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, FlatList, Platform, RefreshControl, Image, ActivityIndicator, TouchableOpacity } from 'react-native';

// Usar una constante directa para la URL de la API - con HTTPS
const API_BASE = 'https://api.acceso.informaticauaint.com/api/ayudantes';

export default function AyudantesScreen() {
  const [ayudantes, setAyudantes] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const loadAyudantes = () => {
    setRefreshing(true);
    setLoading(true);
    setError(null);
    
    console.log("Cargando datos desde:", `${API_BASE}/ayudantes_presentes`);
    
    fetch(`${API_BASE}/ayudantes_presentes`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`Error ${res.status}: ${res.statusText || 'Error del servidor'}`);
        }
        return res.json();
      })
      .then(data => {
        console.log("Datos recibidos:", data);
        
        // Sanitizar y validar los datos recibidos
        const sanitizedData = Array.isArray(data) ? data.map(ayudante => ({
          id: ayudante.id || `aid-${Math.random().toString(36).substring(2, 9)}`,
          nombre: ayudante.nombre || 'Sin nombre',
          apellido: ayudante.apellido || 'Sin apellido',
          email: ayudante.email || 'sin-email@example.com',
          ultima_entrada: ayudante.ultima_entrada || '--:--',
          foto_url: ayudante.foto_url || null,
          estado: 'dentro' // Todos los ayudantes en esta lista están dentro por definición del endpoint
        })) : [];
        
        setAyudantes(sanitizedData);
        setLastUpdated(new Date());
        setRefreshing(false);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error al cargar los ayudantes presentes:', err);
        setError(`No se pudieron cargar los ayudantes: ${err.message}`);
        setRefreshing(false);
        setLoading(false);
        // En caso de error, inicializar ayudantes como un array vacío
        setAyudantes([]);
      });
  };

  useEffect(() => {
    loadAyudantes();
    const interval = setInterval(loadAyudantes, 120000); // Actualizar cada 2 minutos
    return () => clearInterval(interval);
  }, []);

  const onRefresh = () => {
    loadAyudantes();
  };

  const getInitials = (nombre, apellido) => {
    const nombreInit = nombre && nombre.charAt(0) ? nombre.charAt(0) : '';
    const apellidoInit = apellido && apellido.charAt(0) ? apellido.charAt(0) : '';
    return (nombreInit + apellidoInit).toUpperCase();
  };

  // Función para formatear el tiempo de entrada
  const formatEntryTime = (timeString) => {
    if (!timeString || timeString === '--:--') {
      return 'Hora no disponible';
    }
    
    try {
      // Si es una fecha ISO, extraer solo la parte de la hora
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

  // Mostrar indicador de carga mientras se cargan los datos
  if (loading && !refreshing) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#0066CC" />
        <Text style={styles.loadingText}>Cargando ayudantes presentes...</Text>
      </View>
    );
  }

  // Mostrar mensaje de error si ocurrió algún problema
  if (error) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={loadAyudantes}>
          <Text style={styles.retryButtonText}>Reintentar</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Ayudantes en el laboratorio</Text>

      {ayudantes.length === 0 && !refreshing ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>No hay ayudantes en el laboratorio actualmente</Text>
        </View>
      ) : (
        <FlatList
          data={ayudantes}
          keyExtractor={(item, index) => item.email || `item-${index}`}
          numColumns={2}
          columnWrapperStyle={styles.ayudantesRow}
          renderItem={({ item }) => (
            <View style={styles.ayudanteCard}>
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
              <Text style={styles.ayudanteNombre}>{item.nombre || 'Sin nombre'}</Text>
              <Text style={styles.ayudanteApellido}>{item.apellido || 'Sin apellido'}</Text>
              <View style={styles.entradaContainer}>
                <Text style={styles.ayudanteEntrada}>
                  Entrada: {formatEntryTime(item.ultima_entrada)}
                </Text>
                <View style={styles.estadoBadge}>
                  <Text style={styles.estadoText}>Presente</Text>
                </View>
              </View>
            </View>
          )}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            refreshing ? null : (
              <View style={styles.emptyContainer}>
                <Text style={styles.emptyText}>No hay ayudantes en el laboratorio actualmente</Text>
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
  ayudantesRow: {
    justifyContent: 'space-between',
    marginBottom: 15,
  },
  ayudanteCard: {
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
  ayudanteNombre: {
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  ayudanteApellido: {
    fontSize: 16,
    fontWeight: '500',
    textAlign: 'center',
  },
  entradaContainer: {
    marginTop: 5,
    alignItems: 'center',
  },
  ayudanteEntrada: {
    fontSize: 12,
    color: '#666',
    marginBottom: 5,
  },
  estadoBadge: {
    backgroundColor: '#27ae60',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  estadoText: {
    color: 'white',
    fontSize: 10,
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