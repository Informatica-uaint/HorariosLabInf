// app/(tabs)/estudiantes.tsx
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View
} from 'react-native';

// Constante para la URL de la API
const API_BASE = 'https://acceso.informaticauaint.com/api/estudiantes';

// Tipo para los datos de estudiante
type Estudiante = {
  id: string;
  nombre: string;
  apellido: string;
  rut: string;
  carrera: string;
  email: string;
  estado: 'activo' | 'inactivo';
  presente: boolean;
};

export default function EstudiantesScreen() {
  const router = useRouter();
  const [estudiantes, setEstudiantes] = useState<Estudiante[]>([]);
  const [filteredEstudiantes, setFilteredEstudiantes] = useState<Estudiante[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('todos'); // 'todos', 'presentes', 'activos'

  // Cargar datos iniciales
  useEffect(() => {
    loadEstudiantes();
  }, []);

  // Filtrar estudiantes cuando cambia el texto de búsqueda o el filtro
  useEffect(() => {
    filterEstudiantes();
  }, [searchText, filter, estudiantes]);

  // Función para cargar la lista de estudiantes
  const loadEstudiantes = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/estudiantes`);
      if (!response.ok) {
        throw new Error('Error al cargar estudiantes');
      }
      
      const data = await response.json();
      if (Array.isArray(data)) {
        setEstudiantes(data);
      } else {
        throw new Error('Formato de datos inesperado');
      }
    } catch (error) {
      console.error('Error cargando estudiantes:', error);
      setError(`No se pudieron cargar los estudiantes: ${error.message}`);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Filtrar estudiantes según búsqueda y filtro actual
  const filterEstudiantes = () => {
    let filtered = [...estudiantes];
    
    // Aplicar filtro por estado
    if (filter === 'presentes') {
      filtered = filtered.filter(est => est.presente);
    } else if (filter === 'activos') {
      filtered = filtered.filter(est => est.estado === 'activo');
    }
    
    // Aplicar búsqueda de texto
    if (searchText.trim()) {
      const searchLower = searchText.toLowerCase();
      filtered = filtered.filter(est => 
        est.nombre.toLowerCase().includes(searchLower) ||
        est.apellido.toLowerCase().includes(searchLower) ||
        est.rut.toLowerCase().includes(searchLower) ||
        est.carrera.toLowerCase().includes(searchLower)
      );
    }
    
    setFilteredEstudiantes(filtered);
  };

  // Función para refrescar los datos
  const onRefresh = () => {
    setRefreshing(true);
    loadEstudiantes();
  };

  // Renderizar cada item de estudiante
  const renderEstudiante = ({ item }: { item: Estudiante }) => {
    return (
      <TouchableOpacity 
        style={[
          styles.studentCard,
          item.presente && styles.presenteCard,
          item.estado === 'inactivo' && styles.inactivoCard
        ]}
        onPress={() => handleEstudiantePress(item)}
      >
        <View style={styles.studentHeader}>
          <View style={styles.nameContainer}>
            <Text style={styles.studentName}>{item.nombre} {item.apellido}</Text>
            {item.presente && (
              <View style={styles.presenteBadge}>
                <Text style={styles.presenteText}>Presente</Text>
              </View>
            )}
          </View>
          <Ionicons 
            name={item.estado === 'activo' ? "checkmark-circle" : "close-circle"} 
            size={24} 
            color={item.estado === 'activo' ? "#52c41a" : "#ff4d4f"} 
          />
        </View>
        
        <Text style={styles.studentDetail}>RUT: {item.rut}</Text>
        <Text style={styles.studentDetail}>Carrera: {item.carrera}</Text>
        <Text style={styles.studentDetail}>Email: {item.email}</Text>
      </TouchableOpacity>
    );
  };

  // Manejar el press en un estudiante
  const handleEstudiantePress = (estudiante: Estudiante) => {
    Alert.alert(
      `${estudiante.nombre} ${estudiante.apellido}`,
      `¿Qué acción deseas realizar?`,
      [
        {
          text: 'Ver detalles',
          onPress: () => router.push(`/estudiante/${estudiante.id}`)
        },
        {
          text: estudiante.presente ? 'Marcar ausente' : 'Marcar presente',
          onPress: () => togglePresente(estudiante.id, !estudiante.presente)
        },
        {
          text: 'Cancelar',
          style: 'cancel'
        }
      ]
    );
  };

  // Cambiar el estado de presencia de un estudiante
  const togglePresente = async (id: string, presente: boolean) => {
    try {
      const response = await fetch(`${API_BASE}/estudiantes/${id}/presente`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ presente })
      });

      if (!response.ok) {
        throw new Error('Error al actualizar presencia');
      }

      // Actualizar localmente
      setEstudiantes(prevEstudiantes => 
        prevEstudiantes.map(est => 
          est.id === id ? {...est, presente} : est
        )
      );
    } catch (error) {
      console.error('Error al cambiar presencia:', error);
      Alert.alert('Error', 'No se pudo actualizar la presencia del estudiante');
    }
  };

  // Mostrar pantalla de carga
  if (loading && !refreshing) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#0066CC" />
        <Text style={styles.loadingText}>Cargando estudiantes...</Text>
      </View>
    );
  }

  // Mostrar mensaje de error si ocurrió algún problema
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
      <View style={styles.header}>
        <Text style={styles.title}>Estudiantes</Text>
        <TouchableOpacity 
          style={styles.addButton}
          onPress={() => router.push('/nuevo-estudiante')}
        >
          <Ionicons name="add-circle" size={24} color="white" />
          <Text style={styles.addButtonText}>Nuevo</Text>
        </TouchableOpacity>
      </View>

      {/* Barra de búsqueda */}
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color="#999" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Buscar por nombre, RUT o carrera..."
          value={searchText}
          onChangeText={setSearchText}
        />
        {searchText !== '' && (
          <TouchableOpacity onPress={() => setSearchText('')}>
            <Ionicons name="close-circle" size={20} color="#999" />
          </TouchableOpacity>
        )}
      </View>

      {/* Filtros */}
      <View style={styles.filterContainer}>
        <TouchableOpacity 
          style={[styles.filterButton, filter === 'todos' && styles.activeFilter]}
          onPress={() => setFilter('todos')}
        >
          <Text style={[styles.filterText, filter === 'todos' && styles.activeFilterText]}>Todos</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.filterButton, filter === 'presentes' && styles.activeFilter]}
          onPress={() => setFilter('presentes')}
        >
          <Text style={[styles.filterText, filter === 'presentes' && styles.activeFilterText]}>Presentes</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.filterButton, filter === 'activos' && styles.activeFilter]}
          onPress={() => setFilter('activos')}
        >
          <Text style={[styles.filterText, filter === 'activos' && styles.activeFilterText]}>Activos</Text>
        </TouchableOpacity>
      </View>

      {/* Contador de resultados */}
      <Text style={styles.resultCount}>
        {filteredEstudiantes.length} estudiante{filteredEstudiantes.length !== 1 ? 's' : ''} encontrado{filteredEstudiantes.length !== 1 ? 's' : ''}
      </Text>

      {/* Lista de estudiantes */}
      <FlatList
        data={filteredEstudiantes}
        renderItem={renderEstudiante}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.listContainer}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="people" size={60} color="#ccc" />
            <Text style={styles.emptyText}>No se encontraron estudiantes</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 10,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0066CC',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
  },
  addButtonText: {
    color: 'white',
    marginLeft: 5,
    fontWeight: '500',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'white',
    margin: 10,
    paddingHorizontal: 15,
    borderRadius: 25,
    borderWidth: 1,
    borderColor: '#eee',
  },
  searchIcon: {
    marginRight: 10,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 12,
  },
  filterContainer: {
    flexDirection: 'row',
    paddingHorizontal: 10,
    marginBottom: 10,
  },
  filterButton: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 10,
    backgroundColor: '#f0f0f0',
  },
  activeFilter: {
    backgroundColor: '#0066CC',
  },
  filterText: {
    fontWeight: '500',
    color: '#666',
  },
  activeFilterText: {
    color: 'white',
  },
  resultCount: {
    paddingHorizontal: 20,
    marginBottom: 10,
    color: '#666',
    fontStyle: 'italic',
  },
  listContainer: {
    paddingHorizontal: 15,
    paddingBottom: 20,
  },
  studentCard: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 15,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  presenteCard: {
    borderLeftWidth: 5,
    borderLeftColor: '#52c41a',
  },
  inactivoCard: {
    opacity: 0.7,
  },
  studentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  nameContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  studentName: {
    fontSize: 18,
    fontWeight: 'bold',
    marginRight: 8,
  },
  presenteBadge: {
    backgroundColor: '#e6f7ff',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  presenteText: {
    color: '#0066CC',
    fontSize: 12,
    fontWeight: '500',
  },
  studentDetail: {
    color: '#666',
    marginTop: 3,
  },
  loadingText: {
    marginTop: 10,
    color: '#666',
  },
  errorText: {
    color: '#ff4d4f',
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  retryButton: {
    marginTop: 15,
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: '#0066CC',
    borderRadius: 5,
  },
  retryButtonText: {
    color: 'white',
    fontWeight: '500',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 50,
  },
  emptyText: {
    marginTop: 10,
    color: '#999',
    fontSize: 16,
  },
});
