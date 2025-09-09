import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';

const Cumplimiento = () => {
  const [cumplimiento, setCumplimiento] = useState([]);
  const [vista, setVista] = useState('resumen');
  const [lastUpdate, setLastUpdate] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = () => {
    setLoading(true);
    setError(null);
    
    fetch('https://api.acceso.informaticauaint.com/api/ayudantes/cumplimiento')
      .then(response => {
        if (!response.ok) {
          throw new Error('No se pudo conectar al servidor');
        }
        return response.json();
      })
      .then(data => {
        setCumplimiento(data);
        const now = new Date();
        setLastUpdate(now.toLocaleTimeString() + ' ' + now.toLocaleDateString());
        setLoading(false);
      })
      .catch(error => {
        console.error('Error al cargar cumplimiento:', error);
        setError('No pudimos cargar los datos. ¡Intenta de nuevo!');
        setLoading(false);
      });
  };

  // Mapeo actualizado de estados según los requerimientos
  const mapearEstado = (estado) => {
    switch (estado) {
      case 'Cumple': return 'Cumplida';
      case 'Pendiente': return 'Pendiente';
      case 'Incompleto': return 'Incompleto';
      case 'Ausente': return 'No Cumplido';
      case 'No Cumple': return 'No Cumplido';
      case 'No Aplica': return 'No Aplica';
      default: return 'Incompleto';
    }
  };

  const contarPorEstado = (estado) => {
    return cumplimiento.filter(c => mapearEstado(c.estado) === estado).length;
  };

  // Iconos para los estados de semana
  const iconoEstado = {
    'Cumplida': '✅',
    'Pendiente': '⏳',
    'Incompleto': '⚠️',
    'No Cumplido': '❌',
    'No Aplica': '🚫'
  };

  // Colores para los estados de semana
  const colorEstado = {
    'Cumplida': '#4CAF50',
    'Pendiente': '#FFC107',
    'Incompleto': '#FF9800',
    'No Cumplido': '#F44336',
    'No Aplica': '#9E9E9E'
  };

  // Mensajes para los estados de semana
  const mensajeEstado = {
    'Cumplida': '¡Todos los horarios cumplidos!',
    'Pendiente': 'Bloques horarios por cumplir',
    'Incompleto': 'Asistencia parcial a bloques horarios',
    'No Cumplido': 'Sin asistencia registrada',
    'No Aplica': 'Sin horarios asignados'
  };

  // Colores para los estados de bloque
  const colorBloque = {
    'Cumplido': '#4CAF50',
    'Pendiente': '#FFC107',
    'Atrasado': '#FF9800',
    'Incompleto': '#FF9800',
    'Ausente': '#F44336',
    'Cumpliendo': '#2196F3'
  };

  const getTotalCumplimiento = () => {
    const total = cumplimiento.length - contarPorEstado('No Aplica'); // Excluir los "No Aplica"
    const cumpliendo = contarPorEstado('Cumplida');
    return total > 0 ? Math.round((cumpliendo / total) * 100) : 0;
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#0066CC" />
        <Text style={styles.loadingText}>Cargando información...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={fetchData}>
          <Text style={styles.retryButtonText}>Reintentar</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Control de Asistencia</Text>
        <Text style={styles.subtitle}>Monitoreo en tiempo real</Text>
      </View>

      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{cumplimiento.length}</Text>
          <Text style={styles.statLabel}>Total</Text>
        </View>
        <View style={[styles.statCard, {backgroundColor: '#E3F2FD'}]}>
          <Text style={styles.statValue}>{getTotalCumplimiento()}%</Text>
          <Text style={styles.statLabel}>Cumplimiento</Text>
        </View>
      </View>

      <View style={styles.tabContainer}>
        <TouchableOpacity 
          onPress={() => setVista('resumen')} 
          style={[styles.tabButton, vista === 'resumen' && styles.tabButtonActive]}
        >
          <Text style={[styles.tabText, vista === 'resumen' && styles.tabTextActive]}>Resumen</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          onPress={() => setVista('detalle')} 
          style={[styles.tabButton, vista === 'detalle' && styles.tabButtonActive]}
        >
          <Text style={[styles.tabText, vista === 'detalle' && styles.tabTextActive]}>Detalle</Text>
        </TouchableOpacity>
      </View>

      {vista === 'resumen' && (
        <View style={styles.gridContainer}>
          {['Cumplida', 'Pendiente', 'Incompleto', 'No Cumplido', 'No Aplica'].map((estado, index) => (
            <View key={index} style={[styles.gridItem, {borderLeftColor: colorEstado[estado], borderLeftWidth: 5}]}>
              <Text style={styles.estadoIcon}>{iconoEstado[estado]}</Text>
              <View>
                <Text style={styles.estadoTitulo}>{estado}</Text>
                <Text style={styles.estadoContador}>{contarPorEstado(estado)} personas</Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {vista === 'detalle' && (
        <ScrollView style={styles.scrollContainer}>
          {cumplimiento.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateText}>No hay datos de cumplimiento disponibles</Text>
            </View>
          ) : (
            cumplimiento.map((c, index) => {
              const estado = mapearEstado(c.estado);
              return (
                <View key={index} style={[styles.card, {borderLeftColor: colorEstado[estado], borderLeftWidth: 5}]}>
                  <View style={styles.cardHeader}>
                    <Text style={styles.cardTitle}>{c.nombre} {c.apellido}</Text>
                    <View style={[styles.statusBadge, {backgroundColor: colorEstado[estado]}]}>
                      <Text style={styles.statusText}>{estado}</Text>
                    </View>
                  </View>
                  
                  <Text style={styles.statusMessage}>{mensajeEstado[estado]}</Text>
                  
                  {c.bloques && c.bloques.length > 0 ? (
                    <View style={styles.blocksContainer}>
                      <Text style={styles.blocksTitle}>Bloques Horarios:</Text>
                      {/* Usar bloques_info si está disponible o mostrar bloques simples */}
                      {c.bloques_info ? (
                        c.bloques_info.map((bloque, i) => (
                          <View key={i} style={styles.blockRow}>
                            <Text style={styles.blockTime}>{bloque.bloque}</Text>
                            <View style={[styles.blockStatusBadge, {backgroundColor: colorBloque[bloque.estado] || '#9E9E9E'}]}>
                              <Text style={styles.blockStatusText}>{bloque.estado}</Text>
                            </View>
                          </View>
                        ))
                      ) : (
                        c.bloques.map((bloque, i) => (
                          <View key={i} style={styles.blockRow}>
                            <Text style={styles.blockTime}>{bloque}</Text>
                            <View style={[styles.blockStatusBadge, {backgroundColor: '#9E9E9E'}]}>
                              <Text style={styles.blockStatusText}>No Disponible</Text>
                            </View>
                          </View>
                        ))
                      )}
                    </View>
                  ) : (
                    <Text style={styles.noBlocksText}>Sin bloques asignados</Text>
                  )}
                </View>
              );
            })
          )}
        </ScrollView>
      )}

      <View style={styles.footer}>
        <Text style={styles.updateText}>Última actualización: {lastUpdate}</Text>
        <TouchableOpacity style={styles.refreshButton} onPress={fetchData}>
          <Text style={styles.refreshButtonText}>Actualizar datos</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#f5f5f5'
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666'
  },
  errorText: {
    fontSize: 16,
    color: '#d32f2f',
    textAlign: 'center',
    marginBottom: 20
  },
  retryButton: {
    backgroundColor: '#0066CC',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 5
  },
  retryButtonText: {
    color: 'white',
    fontWeight: 'bold'
  },
  header: {
    alignItems: 'center',
    marginBottom: 20
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#0066CC'
  },
  subtitle: {
    fontSize: 14,
    color: '#666'
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20
  },
  statCard: {
    flex: 1,
    backgroundColor: '#E8F5E9',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginHorizontal: 5,
    elevation: 2
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#0066CC'
  },
  statLabel: {
    fontSize: 12,
    color: '#666'
  },
  tabContainer: {
    flexDirection: 'row',
    marginBottom: 20,
    borderRadius: 10,
    overflow: 'hidden',
    backgroundColor: '#E0E0E0'
  },
  tabButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center'
  },
  tabButtonActive: {
    backgroundColor: '#0066CC'
  },
  tabText: {
    fontWeight: '600',
    color: '#555'
  },
  tabTextActive: {
    color: 'white'
  },
  gridContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between'
  },
  gridItem: {
    width: '48%',
    backgroundColor: 'white',
    padding: 15,
    marginBottom: 15,
    borderRadius: 10,
    flexDirection: 'row',
    alignItems: 'center',
    elevation: 2
  },
  estadoIcon: {
    fontSize: 24,
    marginRight: 10
  },
  estadoTitulo: {
    fontSize: 14,
    fontWeight: 'bold'
  },
  estadoContador: {
    fontSize: 12,
    color: '#666'
  },
  scrollContainer: {
    flex: 1
  },
  emptyState: {
    padding: 40,
    alignItems: 'center'
  },
  emptyStateText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center'
  },
  card: {
    backgroundColor: 'white',
    padding: 15,
    marginBottom: 15,
    borderRadius: 10,
    elevation: 2
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold'
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20
  },
  statusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold'
  },
  statusMessage: {
    fontSize: 14,
    fontStyle: 'italic',
    marginBottom: 10,
    color: '#666'
  },
  blocksContainer: {
    marginTop: 10
  },
  blocksTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 5
  },
  blockRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 5,
    borderBottomWidth: 1,
    borderBottomColor: '#eee'
  },
  blockTime: {
    fontSize: 14
  },
  blockStatusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 15
  },
  blockStatusText: {
    fontSize: 11,
    color: 'white',
    fontWeight: 'bold'
  },
  noBlocksText: {
    fontSize: 14,
    fontStyle: 'italic',
    color: '#999',
    textAlign: 'center',
    marginTop: 10
  },
  footer: {
    marginTop: 15,
    alignItems: 'center'
  },
  updateText: {
    fontSize: 12,
    color: '#888',
    marginBottom: 10
  },
  refreshButton: {
    backgroundColor: '#0066CC',
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 20
  },
  refreshButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600'
  }
});

export default Cumplimiento;