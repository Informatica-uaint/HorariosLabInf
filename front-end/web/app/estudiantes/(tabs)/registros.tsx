// app/(tabs)/registros.tsx
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import React, { useEffect, useState } from 'react';
import {
    ActivityIndicator,
    FlatList,
    Modal,
    RefreshControl,
    StyleSheet,
    Text,
    TextInput,
    TouchableOpacity,
    View,
    Dimensions
} from 'react-native';

const { width } = Dimensions.get('window');

// Constante para la URL de la API
const API_BASE = 'https://acceso.informaticauaint.com/api/estudiantes';

// Tipo para los datos de registro
type Registro = {
  id: string;
  estudianteId: string;
  nombreEstudiante: string;
  apellidoEstudiante: string;
  rutEstudiante: string;
  tipoRegistro: 'entrada' | 'salida';
  horaRegistro: string;
  fecha: string;
  ayudanteId?: string;
  nombreAyudante?: string;
};

export default function RegistrosScreen() {
  const router = useRouter();
  const [registros, setRegistros] = useState<Registro[]>([]);
  const [filteredRegistros, setFilteredRegistros] = useState<Registro[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('hoy'); // 'hoy', 'semana', 'mes'
  const [showFilterModal, setShowFilterModal] = useState(false);

  // Cargar datos iniciales
  useEffect(() => {
    loadRegistros();
  }, [filter]);

  // Filtrar registros cuando cambia el texto de búsqueda
  useEffect(() => {
    filterRegistros();
  }, [searchText, registros]);

  // Función para cargar la lista de registros
  const loadRegistros = async () => {
    setLoading(true);
    setError(null);
  
    try {
      // Construir el endpoint según el filtro
      let endpoint = `${API_BASE}/registros`;
    
      if (filter === 'hoy') {
        endpoint = `${API_BASE}/registros_hoy`;
      } else if (filter === 'semana') {
        endpoint = `${API_BASE}/registros_semana`;
      } else if (filter === 'mes') {
        endpoint = `${API_BASE}/registros_mes`;
      }
    
      const response = await fetch(endpoint);
      if (!response.ok) {
        throw new Error('Error al cargar registros');
      }
    
      const result = await response.json();
      console.log('Respuesta completa:', result); // Para debug
    
    // ✅ CORRECCIÓN: Acceder a result.data en lugar de result directamente
      if (result.status === 'success' && Array.isArray(result.data)) {
        setRegistros(result.data);
        setFilteredRegistros(result.data);
      } else {
        console.error('Estructura de datos inesperada:', result);
        throw new Error('Formato de datos inesperado');
      }
    } catch (error) {
      console.error('Error cargando registros:', error);
      setError(`No se pudieron cargar los registros: ${error.message}`);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Filtrar registros según búsqueda
  const filterRegistros = () => {
    if (!searchText.trim()) {
      setFilteredRegistros(registros);
      return;
    }
    
    const searchLower = searchText.toLowerCase();
    const filtered = registros.filter(reg => 
      reg.nombreEstudiante.toLowerCase().includes(searchLower) ||
      reg.apellidoEstudiante.toLowerCase().includes(searchLower) ||
      reg.rutEstudiante.toLowerCase().includes(searchLower) ||
      (reg.nombreAyudante && reg.nombreAyudante.toLowerCase().includes(searchLower))
    );
    
    setFilteredRegistros(filtered);
  };

  // Función para refrescar los datos
  const onRefresh = () => {
    setRefreshing(true);
    loadRegistros();
  };

  // Renderizar cada item de registro
  const renderRegistro = ({ item }: { item: Registro }) => {
    return (
      <View 
        style={[
          styles.registroCard,
          item.tipoRegistro === 'entrada' ? styles.entradaCard : styles.salidaCard
        ]}
      >
        <View style={styles.registroHeader}>
          <View style={styles.tipoContainer}>
            <Ionicons 
              name={item.tipoRegistro === 'entrada' ? "log-in-outline" : "log-out-outline"} 
              size={20} 
              color={item.tipoRegistro === 'entrada' ? "#52c41a" : "#ff4d4f"} 
            />
            <Text style={[
              styles.tipoText,
              item.tipoRegistro === 'entrada' ? styles.entradaText : styles.salidaText
            ]}>
              {item.tipoRegistro === 'entrada' ? 'Entrada' : 'Salida'}
            </Text>
          </View>
          <Text style={styles.horaRegistro}>
            {new Date(item.horaRegistro).toLocaleTimeString('es-CL', {
              hour: '2-digit', 
              minute: '2-digit'
            })}
          </Text>
        </View>
        
        <Text style={styles.estudianteNombre}>
          {item.nombreEstudiante} {item.apellidoEstudiante}
        </Text>
        <Text style={styles.registroDetail}>RUT: {item.rutEstudiante}</Text>
        <Text style={styles.registroDetail}>
          Fecha: {new Date(item.fecha).toLocaleDateString('es-CL')}
        </Text>
        
        {item.nombreAyudante && (
          <Text style={styles.registroDetail}>
            Ayudante: {item.nombreAyudante}
          </Text>
        )}
      </View>
    );
  };

  // Agrupar registros por fecha
  const groupedRegistros = () => {
    const grouped: { [key: string]: Registro[] } = {};
    
    filteredRegistros.forEach(registro => {
      const fecha = new Date(registro.fecha).toLocaleDateString('es-CL');
      if (!grouped[fecha]) {
        grouped[fecha] = [];
      }
      grouped[fecha].push(registro);
    });
    
    return Object.entries(grouped).map(([fecha, registros]) => ({
      fecha,
      registros
    }));
  };

  // Renderizar sección de fecha
  const renderDateSection = ({ item }: { item: { fecha: string, registros: Registro[] } }) => {
    return (
      <View style={styles.dateSection}>
        <View style={styles.dateBanner}>
          <Text style={styles.dateText}>{item.fecha}</Text>
          <Text style={styles.countText}>
            {item.registros.length} registro{item.registros.length !== 1 ? 's' : ''}
          </Text>
        </View>
        
        <FlatList
          data={item.registros}
          renderItem={renderRegistro}
          keyExtractor={reg => reg.id}
          scrollEnabled={false}
        />
      </View>
    );
  };

  // Mostrar pantalla de carga
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

  // Obtener el título del filtro actual
  const getFilterTitle = () => {
    switch (filter) {
      case 'hoy':
        return 'Hoy';
      case 'semana':
        return 'Esta semana';
      case 'mes':
        return 'Este mes';
      default:
        return 'Registros';
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Registros</Text>
        <TouchableOpacity 
          style={styles.filterButton}
          onPress={() => setShowFilterModal(true)}
        >
          <Ionicons name="calendar-outline" size={20} color="white" />
          <Text style={styles.filterButtonText}>{getFilterTitle()}</Text>
          <Ionicons name="chevron-down" size={16} color="white" />
        </TouchableOpacity>
      </View>

      {/* Barra de búsqueda */}
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color="#999" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Buscar por nombre o RUT..."
          value={searchText}
          onChangeText={setSearchText}
        />
        {searchText !== '' && (
          <TouchableOpacity onPress={() => setSearchText('')}>
            <Ionicons name="close-circle" size={20} color="#999" />
          </TouchableOpacity>
        )}
      </View>

      {/* Contador de resultados */}
      <Text style={styles.resultCount}>
        {filteredRegistros.length} registro{filteredRegistros.length !== 1 ? 's' : ''} encontrado{filteredRegistros.length !== 1 ? 's' : ''}
      </Text>

      {/* Lista de registros agrupados por fecha */}
      <FlatList
        data={groupedRegistros()}
        renderItem={renderDateSection}
        keyExtractor={item => item.fecha}
        contentContainerStyle={styles.listContainer}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="document-text" size={60} color="#ccc" />
            <Text style={styles.emptyText}>No se encontraron registros</Text>
          </View>
        }
      />

      {/* Modal de filtro */}
      <Modal
        visible={showFilterModal}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setShowFilterModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Filtrar por fecha</Text>
            
            <TouchableOpacity 
              style={[styles.filterOption, filter === 'hoy' && styles.selectedFilter]}
              onPress={() => {
                setFilter('hoy');
                setShowFilterModal(false);
              }}
            >
              <Text style={styles.filterOptionText}>Hoy</Text>
              {filter === 'hoy' && <Ionicons name="checkmark" size={20} color="#0066CC" />}
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[styles.filterOption, filter === 'semana' && styles.selectedFilter]}
              onPress={() => {
                setFilter('semana');
                setShowFilterModal(false);
              }}
            >
              <Text style={styles.filterOptionText}>Esta semana</Text>
              {filter === 'semana' && <Ionicons name="checkmark" size={20} color="#0066CC" />}
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[styles.filterOption, filter === 'mes' && styles.selectedFilter]}
              onPress={() => {
                setFilter('mes');
                setShowFilterModal(false);
              }}
            >
              <Text style={styles.filterOptionText}>Este mes</Text>
              {filter === 'mes' && <Ionicons name="checkmark" size={20} color="#0066CC" />}
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.closeButton}
              onPress={() => setShowFilterModal(false)}
            >
              <Text style={styles.closeButtonText}>Cerrar</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
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
    fontSize: width > 400 ? 24 : 20,
    fontWeight: 'bold',
    color: '#333',
  },
  filterButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0066CC',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
  },
  filterButtonText: {
    color: 'white',
    marginHorizontal: 5,
    fontWeight: '500',
    fontSize: 14,
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
    fontSize: 16,
  },
  resultCount: {
    paddingHorizontal: 20,
    marginBottom: 10,
    color: '#666',
    fontStyle: 'italic',
    fontSize: 14,
  },
  listContainer: {
    paddingHorizontal: 15,
    paddingBottom: 20,
  },
  dateSection: {
    marginBottom: 20,
  },
  dateBanner: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    paddingHorizontal: 15,
    backgroundColor: '#e6f7ff',
    borderRadius: 5,
    marginBottom: 10,
  },
  dateText: {
    fontWeight: 'bold',
    color: '#0066CC',
    fontSize: 16,
  },
  countText: {
    color: '#666',
    fontSize: 14,
  },
  registroCard: {
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
  entradaCard: {
    borderLeftWidth: 5,
    borderLeftColor: '#52c41a',
  },
  salidaCard: {
    borderLeftWidth: 5,
    borderLeftColor: '#ff4d4f',
  },
  registroHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  tipoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  tipoText: {
    marginLeft: 5,
    fontWeight: '500',
    fontSize: 16,
  },
  entradaText: {
    color: '#52c41a',
  },
  salidaText: {
    color: '#ff4d4f',
  },
  horaRegistro: {
    fontWeight: 'bold',
    fontSize: 16,
  },
  estudianteNombre: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 3,
  },
  registroDetail: {
    color: '#666',
    marginTop: 3,
    fontSize: 14,
  },
  loadingText: {
    marginTop: 10,
    color: '#666',
    fontSize: 16,
  },
  errorText: {
    color: '#ff4d4f',
    textAlign: 'center',
    paddingHorizontal: 20,
    fontSize: 16,
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
    fontSize: 16,
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
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    width: '80%',
    maxWidth: 400,
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    textAlign: 'center',
  },
  filterOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 5,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  selectedFilter: {
    backgroundColor: '#f0f8ff',
  },
  filterOptionText: {
    fontSize: 16,
  },
  closeButton: {
    marginTop: 15,
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    paddingVertical: 10,
    borderRadius: 5,
  },
  closeButtonText: {
    color: '#333',
    fontWeight: '500',
    fontSize: 16,
  },
});