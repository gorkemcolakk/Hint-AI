import { Stack } from 'expo-router';

import { Colors } from '@/constants/theme';

export default function GuardianLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: Colors.guardian },
        headerTintColor: Colors.onPrimary,
      }}>
      <Stack.Screen name="children/index" options={{ title: 'Çocuklarım' }} />
      <Stack.Screen name="children/new" options={{ title: 'Çocuk ekle' }} />
      <Stack.Screen name="children/[id]" options={{ title: 'Çocuk profili' }} />
    </Stack>
  );
}
