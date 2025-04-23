// app/horas.tsx
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList, RefreshControl, TouchableOpacity, Platform, ActivityIndicator } from 'react-native';

// Usar una constante directa para la URL de la API
const API_BASE = 'https://10.0.3.54:5000';

export default function HorasAcumuladasScreen() {
  const [horasData, setHorasData] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState('horas');

  const loadHorasAcumuladas = () => {
    setRefreshing(true);
    setLoading(true);
    setError(null);
    
    console.log("Cargando datos desde:", `${API_BASE}/horas_acumuladas`);
    
    fetch(`${API_BASE}/horas_acumuladas`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`Error ${res.status}: ${res.statusText || 'Error del servidor'}`);
        }
        return res.json();
      })
      .then(data => {
        console.log("Datos recibidos:", data);
        setHorasData(Array.isArray(data) ? data : []);
        setRefreshing(false);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error loading horas acumuladas:', err);
        setError(`No se pudieron cargar las horas acumuladas: ${err.message}`);
        setRefreshing(false);
        setLoading(false);
        // En caso de error, inicializar horasData como un array vacío
        setHorasData([]);
      });
  };

  useEffect(() => {
    loadHorasAcumuladas();
    const interval = setInterval(loadHorasAcumuladas, 900000);
    return () => clearInterval(interval);
  }, []);

  const onRefresh = () => {
    loadHorasAcumuladas();
  };

  const sortedData = [...horasData].sort((a, b) => {
    if (sortBy === 'horas') {
      return b.horas_totales - a.horas_totales;
    } else {
      return a.nombre.localeCompare(b.nombre);
    }
  });

  // Mostrar indicador de carga mientras se cargan los datos
  if (loading && !refreshing) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#0066CC" />
        <Text style={styles.loadingText}>Cargando horas acumuladas...</Text>
      </View>
    );
  }

  // Mostrar mensaje de error si ocurrió algún problema
  if (error) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={loadHorasAcumuladas}>
          <Text style={styles.retryButtonText}>Reintentar</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Horas Acumuladas</Text>

      <View style={styles.sortButtons}>
        <TouchableOpacity 
          style={[styles.sortButton, sortBy === 'horas' && styles.sortActive]}
          onPress={() => setSortBy('horas')}
        >
          <Text style={[styles.sortButtonText, sortBy === 'horas' && styles.sortActiveText]}>Por Horas</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.sortButton, sortBy === 'nombre' && styles.sortActive]}
          onPress={() => setSortBy('nombre')}
        >
          <Text style={[styles.sortButtonText, sortBy === 'nombre' && styles.sortActiveText]}>Por Nombre</Text>
        </TouchableOpacity>
      </View>

      {sortedData.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>No hay datos de horas acumuladas</Text>
        </View>
      ) : (
        <FlatList
          data={sortedData}
          keyExtractor={(item, index) => item.email || `item-${index}`}
          renderItem={({ item }) => (
            <View style={styles.horasItem}>
              <View style={styles.horasInfo}>
                <Text style={styles.horasNombre}>{item.nombre} {item.apellido}</Text>
                <Text style={styles.horasEmail}>{item.email}</Text>
              </View>
              <View style={styles.horasStats}>
                <View style={styles.horaStat}>
                  <Text style={styles.horasStatValue}>{item.horas_totales || 0}</Text>
                  <Text style={styles.horasStatLabel}>Horas</Text>
                </View>
                <View style={styles.horaStat}>
                  <Text style={styles.horasStatValue}>{item.dias_asistidos || 0}</Text>
                  <Text style={styles.horasStatLabel}>Días</Text>
                </View>
              </View>
            </View>
          )}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        />
      )}

      <Text style={styles.lastUpdate}>Última actualización: {new Date().toLocaleTimeString()}</Text>
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
  sortButtons: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 15,
  },
  sortButton: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    marginHorizontal: 10,
    backgroundColor: 'white',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  sortActive: {
    backgroundColor: '#1890ff',
    borderColor: '#1890ff',
  },
  sortButtonText: {
    color: '#333',
  },
  sortActiveText: {
    color: 'white',
  },
  horasItem: {
    padding: 15,
    marginBottom: 10,
    backgroundColor: 'white',
    borderRadius: 5,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 1.5,
    elevation: 2,
  },
  horasInfo: {
    flex: 2,
  },
  horasNombre: {
    fontSize: 16,
    fontWeight: '500',
  },
  horasEmail: {
    fontSize: 12,
    color: '#666',
  },
  horasStats: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  horaStat: {
    alignItems: 'center',
  },
  horasStatValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1890ff',
  },
  horasStatLabel: {
    fontSize: 12,
    color: '#666',
  },
  lastUpdate: {
    textAlign: 'center',
    fontSize: 12,
    color: '#999',
    marginTop: 10,
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
});
