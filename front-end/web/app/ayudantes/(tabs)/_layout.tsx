import React from 'react';
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { TouchableOpacity, useWindowDimensions } from 'react-native';
import { useRouter } from 'expo-router';

export default function AyudantesTabLayout() {
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
        tabBarInactiveTintColor: '#7f8c8d',
        tabBarShowLabel: !hideLabels,
        tabBarLabelStyle: {
          fontSize: hideLabels ? 0 : 11,
        },
        tabBarItemStyle: {
          minWidth: hideLabels ? 56 : 72,
        },
        tabBarStyle: {
          height: hideLabels ? 58 : 64,
          paddingVertical: hideLabels ? 4 : 6,
        },
        tabBarHideOnKeyboard: true,
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
          tabBarLabel: "Generador",
        }}
      />
      <Tabs.Screen
        name="registros"
        options={{
          title: "Registros",
          tabBarLabel: "Registros",
        }}
      />
      <Tabs.Screen
        name="cumplimiento"
        options={{
          title: "Cumplimiento",
          tabBarLabel: "Cumpl.",
        }}
      />
      <Tabs.Screen
        name="horas"
        options={{
          title: "Horas",
          tabBarLabel: "Horas",
        }}
      />
      <Tabs.Screen
        name="ayudantes"
        options={{
          title: "Ayudantes",
          tabBarLabel: "Ayudantes",
        }}
      />
    </Tabs>
  );
}
