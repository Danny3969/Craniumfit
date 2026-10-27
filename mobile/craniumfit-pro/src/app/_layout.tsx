import React from 'react';
import { Slot } from 'expo-router';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { ProAuthProvider } from '../context/AuthContext';

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <ProAuthProvider>
        <Slot />
      </ProAuthProvider>
    </SafeAreaProvider>
  );
}
