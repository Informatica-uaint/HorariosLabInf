// app/(tabs)/index.tsx
import React from 'react';
import {
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  useWindowDimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

export default function PortalSelector() {
  const router = useRouter();
  const { width } = useWindowDimensions();
  const safeWidth = width > 0 ? width : 360;
  const cardWidth = Math.min(safeWidth - 32, 520);
  const isCompact = safeWidth < 400;

  const navigateToEstudiantes = () => {
    router.push('/estudiantes');
  };

  const navigateToAyudantes = () => {
    router.push('/ayudantes');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.container}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text style={[styles.title, isCompact && styles.titleCompact]}>
            Sistema de Control de Acceso
          </Text>
          <Text style={styles.subtitle}>Laboratorio de Informática</Text>
          <Text style={styles.description}>
            Selecciona el portal correspondiente para acceder al sistema
          </Text>
        </View>

        <View style={styles.buttonsContainer}>
          <TouchableOpacity 
            style={[
              styles.portalButton,
              styles.estudiantesButton,
              { width: cardWidth },
            ]}
            onPress={navigateToEstudiantes}
            activeOpacity={0.8}
          >
            <View style={styles.iconContainer}>
              <Ionicons name="school-outline" size={60} color="white" />
            </View>
            <Text style={styles.buttonTitle}>Portal Estudiantes</Text>
            <Text style={styles.buttonDescription}>
              Generación de QR, consulta de estudiantes y registros de acceso
            </Text>
            <View style={styles.arrowContainer}>
              <Ionicons name="arrow-forward" size={24} color="white" />
            </View>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[
              styles.portalButton,
              styles.ayudantesButton,
              { width: cardWidth },
            ]}
            onPress={navigateToAyudantes}
            activeOpacity={0.8}
          >
            <View style={styles.iconContainer}>
              <Ionicons name="people-outline" size={60} color="white" />
            </View>
            <Text style={styles.buttonTitle}>Portal Ayudantes</Text>
            <Text style={styles.buttonDescription}>
              QR de ayudantes, registros, cumplimiento y control de horas
            </Text>
            <View style={styles.arrowContainer}>
              <Ionicons name="arrow-forward" size={24} color="white" />
            </View>
          </TouchableOpacity>
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Universidad Adolfo Ibañez - Facultad de Ciencias
          </Text>
          <Text style={styles.footerSubtext}>
            Departamento de informatica
          </Text>
        </View>

      </ScrollView>
      <StatusBar style="dark" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#f5f7fa',
  },
  container: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingBottom: 40,
    alignItems: 'center',
  },
  header: {
    alignItems: 'center',
    paddingTop: 40,
    paddingBottom: 20,
    width: '100%',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#2c3e50',
    textAlign: 'center',
    marginBottom: 8,
  },
  titleCompact: {
    fontSize: 24,
  },
  subtitle: {
    fontSize: 18,
    color: '#34495e',
    marginBottom: 12,
    fontWeight: '600',
  },
  description: {
    fontSize: 16,
    color: '#7f8c8d',
    textAlign: 'center',
    lineHeight: 22,
    paddingHorizontal: 20,
  },
  buttonsContainer: {
    width: '100%',
    alignItems: 'center',
    paddingVertical: 20,
  },
  portalButton: {
    minHeight: 180,
    borderRadius: 20,
    paddingVertical: 30,
    paddingHorizontal: 24,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
    position: 'relative',
    marginBottom: 24,
  },
  estudiantesButton: {
    backgroundColor: '#3498db',
  },
  ayudantesButton: {
    backgroundColor: '#e74c3c',
  },
  iconContainer: {
    marginBottom: 15,
  },
  buttonTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 10,
    textAlign: 'center',
  },
  buttonDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    lineHeight: 20,
    paddingHorizontal: 10,
  },
  arrowContainer: {
    position: 'absolute',
    right: 25,
    top: '50%',
    transform: [{ translateY: -12 }],
  },
  footer: {
    alignItems: 'center',
    paddingVertical: 30,
  },
  footerText: {
    fontSize: 14,
    color: '#7f8c8d',
    fontWeight: '600',
  },
  footerSubtext: {
    fontSize: 12,
    color: '#95a5a6',
    marginTop: 4,
  },
});
