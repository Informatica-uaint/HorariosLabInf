import React from 'react';
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { TouchableOpacity, useWindowDimensions } from 'react-native';
import { useRouter } from 'expo-router';

export default function EstudiantesTabLayout() {
  const router = useRouter();
  const { width } = useWindowDimensions();
  const hideLabels = width < 392;

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
        tabBarIcon: ({ color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap = 'help-outline';

          if (route.name === 'index') {
            iconName = 'qr-code-outline';
          } else if (route.name === 'estudiantes') {
            iconName = 'people-outline';
          } else if (route.name === 'registros') {
            iconName = 'list-outline';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#3498db',
        tabBarInactiveTintColor: '#7f8c8d',
        tabBarShowLabel: !hideLabels,
        tabBarLabelStyle: {
          fontSize: hideLabels ? 0 : 11,
        },
        tabBarItemStyle: {
          minWidth: hideLabels ? 64 : 82,
        },
        tabBarStyle: {
          height: hideLabels ? 58 : 66,
          paddingVertical: hideLabels ? 4 : 8,
        },
        tabBarHideOnKeyboard: true,
        headerStyle: {
          backgroundColor: '#3498db',
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
        name="estudiantes"
        options={{
          title: "Estudiantes",
        }}
      />
      <Tabs.Screen
        name="registros"
        options={{
          title: "Registros",
        }}
      />
    </Tabs>
  );
}
