import { Stack } from 'expo-router';

import { Colors } from '@/constants/theme';

export default function TeacherLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: Colors.teacher },
        headerTintColor: Colors.onPrimary,
        headerBackButtonDisplayMode: 'minimal',
      }}>
      <Stack.Screen name="classes/index" options={{ title: 'Sınıflarım' }} />
      <Stack.Screen name="classes/[id]" options={{ title: 'Sınıf' }} />
    </Stack>
  );
}
