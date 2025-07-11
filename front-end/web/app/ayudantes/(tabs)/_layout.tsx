import React from 'react';
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';

export default function AyudantesTabLayout() {
  const router = useRouter();

  const HeaderBackButton = () => (
    <TouchableOpacity
      onPress={() => router.push('/')}
      style={{ marginLeft: 10 }}
    >
      <Ionicons name="home" size={24} color="white" />
    </TouchableOpacity>
  );

  return (
    <Tabs
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap = 'help-outline';

          if (route.name === 'index') {
            iconName = 'qr-code-outline';
          } else if (route.name === 'registros') {
            iconName = 'list-outline';
          } else if (route.name === 'cumplimiento') {
            iconName = 'checkmark-circle-outline';
          } else if (route.name === 'horas') {
            iconName = 'time-outline';
          } else if (route.name === 'ayudantes') {
            iconName = 'people-outline';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#e74c3c',
        tabBarInactiveTintColor: 'gray',
        headerStyle: {
          backgroundColor: '#e74c3c',
        },
        headerTintColor: '#fff',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
        headerLeft: () => <HeaderBackButton />,
      })}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Generador QR",
        }}
      />
      <Tabs.Screen
        name="registros"
        options={{
          title: "Registros",
        }}
      />
      <Tabs.Screen
        name="cumplimiento"
        options={{
          title: "Cumplimiento",
        }}
      />
      <Tabs.Screen
        name="horas"
        options={{
          title: "Horas",
        }}
      />
      <Tabs.Screen
        name="ayudantes"
        options={{
          title: "Ayudantes",
        }}
      />
    </Tabs>
  );
}