// app/registros.tsx
import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, FlatList, RefreshControl, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { Platform } from 'react-native';

// Usar HTTPS para todas las conexiones API
const API_BASE = 'https://api.acceso.informaticauaint.com/api/ayudantes';

export default function RegistrosScreen() {
  const [registros, setRegistros] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filtroPersona, setFiltroPersona] = useState(null);
  // Add a state for last update time to ensure consistency between server and client
  const [lastUpdateTime, setLastUpdateTime] = useState('');

  const loadRegistros = () => {
    setRefreshing(true);
    setLoading(true);
    setError(null);
    
    fetch(`${API_BASE}/registros_hoy`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`Error ${res.status}: ${res.statusText || 'Error del servidor'}`);
        }
        return res.json();
      })
      .then(data => {
        // Asegurarse de que data es un array y verificar los datos
        const registrosArray = Array.isArray(data) ? data : [];
        
        // Validar y sanitizar cada registro para evitar problemas de renderizado
        const sanitizedRegistros = registrosArray.map(registro => ({
          id: registro.id || `id-${Math.random().toString(36).substr(2, 9)}`,
          fecha: registro.fecha || '',
          hora: registro.hora || '',
          dia: registro.dia || '',
          nombre: registro.nombre || 'Sin nombre',
          apellido: registro.apellido || 'Sin apellido',
          email: registro.email || 'sin-email@example.com',
          tipo: registro.tipo || '',
          estado: registro.estado || ''
        }));
        
        setRegistros(sanitizedRegistros);
        setRefreshing(false);
        setLoading(false);
        // Update last update time after data is loaded
        setLastUpdateTime(new Date().toLocaleTimeString());
      })
      .catch(err => {
        console.error('Error al cargar registros:', err);
        setError(`No se pudieron cargar los registros: ${err.message}`);
        setRefreshing(false);
        setLoading(false);
        // En caso de error, inicializar registros como un array vacío
        setRegistros([]);
      });
  };

  // Only run on the client side
  useEffect(() => {
    // Set initial last update time to prevent hydration mismatch
    setLastUpdateTime(new Date().toLocaleTimeString());
    
    // Use useEffect to ensure this only runs on the client
    loadRegistros();
    
    // Configurar intervalo para recargar datos
    const interval = setInterval(loadRegistros, 300000); // 5 minutos
    
    // Limpiar intervalo cuando el componente se desmonte
    return () => {
      clearInterval(interval);
    };
  }, []);

  const onRefresh = () => {
    loadRegistros();
  };

  const getUniquePersonas = () => {
    // Verificar que registros sea un array válido
    if (!Array.isArray(registros) || registros.length === 0) {
      return [];
    }
    
    // Filtrar cualquier registro sin email válido
    const validRegistros = registros.filter(item => item && item.email);
    
    // Obtener emails únicos
    const uniqueEmails = [...new Set(validRegistros.map(item => item.email))];
    
    // Mapear a objetos con nombre y email
    return uniqueEmails.map(email => {
      const persona = validRegistros.find(r => r.email === email);
      if (!persona) return { email, nombre: 'Desconocido' };
      
      return {
        email,
        nombre: `${persona.nombre || ''} ${persona.apellido || ''}`.trim() || 'Desconocido',
      };
    });
  };

  // Filtrar registros por persona seleccionada
  const filteredRegistros = filtroPersona 
    ? registros.filter(item => item && item.email === filtroPersona)
    : registros;

  // Mostrar indicador de carga mientras se cargan los datos
  if (loading && !refreshing) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#0066CC" />
        <Text style={styles.loadingText}>Cargando registros...</Text>
      </View>
    );
  }

  // Mostrar mensaje de error si ocurrió algún problema
  if (error) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={loadRegistros}>
          <Text style={styles.retryButtonText}>Reintentar</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Obtener personas únicas para filtros
  const uniquePersonas = getUniquePersonas();

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Registros de Hoy</Text>

      <ScrollView horizontal style={styles.filterContainer}>
        <TouchableOpacity 
          style={[styles.filterButton, filtroPersona === null && styles.filterActive]} 
          onPress={() => setFiltroPersona(null)}
        >
          <Text style={styles.filterText}>Todos</Text>
        </TouchableOpacity>

        {uniquePersonas.map((persona, idx) => (
          <TouchableOpacity 
            key={`persona-${idx}-${persona.email}`}
            style={[styles.filterButton, filtroPersona === persona.email && styles.filterActive]}
            onPress={() => setFiltroPersona(persona.email)}
          >
            <Text style={styles.filterText}>{persona.nombre}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {!Array.isArray(filteredRegistros) || filteredRegistros.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>No hay registros para mostrar</Text>
        </View>
      ) : (
        <FlatList
          data={filteredRegistros}
          keyExtractor={(item, index) => `${item?.id || `reg-${index}`}`}
          renderItem={({ item }) => (
            item ? (
              <View style={styles.registroItem}>
                <Text style={styles.registroNombre}>
                  {item.nombre || ''} {item.apellido || ''}
                </Text>
                <Text style={styles.registroHora}>{item.hora || '--:--'}</Text>
                <Text style={[
                  styles.registroTipo,
                  item.tipo === 'Entrada' ? styles.entradaText : styles.salidaText
                ]}>
                  {item.tipo || 'Desconocido'}
                </Text>
              </View>
            ) : null
          )}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        />
      )}

      {/* Use the state variable for last update time to ensure hydration consistency */}
      <Text style={styles.lastUpdate}>
        Última actualización: {lastUpdateTime}
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
  filterContainer: {
    marginBottom: 10,
    maxHeight: 50,
  },
  filterButton: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    marginRight: 10,
    backgroundColor: 'white',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  filterActive: {
    backgroundColor: '#1890ff',
    borderColor: '#1890ff',
  },
  filterText: {
    color: '#333',
  },
  registroItem: {
    padding: 15,
    marginBottom: 10,
    backgroundColor: 'white',
    borderRadius: 5,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  registroNombre: {
    flex: 2,
    fontWeight: '500',
  },
  registroHora: {
    flex: 1,
    textAlign: 'center',
  },
  registroTipo: {
    flex: 1,
    textAlign: 'right',
    fontWeight: '500',
  },
  entradaText: {
    color: '#27ae60',  // Color verde para entradas
  },
  salidaText: {
    color: '#e67e22',  // Color naranja para salidas
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