import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { restoreSession } from '@/auth/auth';
import { useSessionState } from '@/auth/session-store';
import { Colors } from '@/constants/theme';

export default function RootLayout() {
  const [queryClient] = useState(
    () => new QueryClient({ defaultOptions: { queries: { retry: 1 } } }),
  );
  const state = useSessionState();
  const session = state.status === 'ready' ? state.session : null;
  const sessionKind = state.status === 'ready' ? (session?.kind ?? 'none') : 'loading';

  useEffect(() => {
    void restoreSession();
  }, []);

  // Oturum türü değişince (çıkış, başka hesap, çocuk moduna geçiş) önbellekteki veriler silinir.
  useEffect(() => {
    queryClient.clear();
  }, [sessionKind, queryClient]);

  if (state.status === 'loading') {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color={Colors.guardian} />
      </View>
    );
  }

  // Erişim kuralları tek yerde: koruması kalkan ekranlar geçmişten silinir ve kullanıcı
  // index'e döner; index de oturuma göre doğru ekrana yönlendirir.
  return (
    <QueryClientProvider client={queryClient}>
      <StatusBar style="dark" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="pair" />
        <Stack.Protected guard={session === null}>
          <Stack.Screen name="welcome" />
          <Stack.Screen name="login" options={{ headerShown: true, title: 'Giriş yap' }} />
          <Stack.Screen name="register" options={{ headerShown: true, title: 'Kayıt ol' }} />
        </Stack.Protected>
        <Stack.Protected guard={session?.kind === 'guardian'}>
          <Stack.Screen name="(guardian)" />
        </Stack.Protected>
        <Stack.Protected guard={session?.kind === 'child'}>
          <Stack.Screen name="(child)" />
        </Stack.Protected>
      </Stack>
    </QueryClientProvider>
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.background,
  },
});
