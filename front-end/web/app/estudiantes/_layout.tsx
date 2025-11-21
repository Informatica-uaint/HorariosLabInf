import React from 'react';
import { Stack } from 'expo-router';
import { TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

export default function EstudiantesLayout() {
  const router = useRouter();

  const HeaderBackButton = () => (
    <TouchableOpacity
      onPress={() => router.push('/')}
      style={{ marginLeft: 10 }}
    >
      <Ionicons name="arrow-back" size={24} color="white" />
    </TouchableOpacity>
  );

  return (
    <Stack
      screenOptions={{
        headerStyle: {
          backgroundColor: '#3498db',
        },
        headerTintColor: '#fff',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
        headerLeft: () => <HeaderBackButton />,
      }}
    >
      <Stack.Screen 
        name="(tabs)" 
        options={{ 
          headerShown: false 
        }} 
      />
    </Stack>
  );
}