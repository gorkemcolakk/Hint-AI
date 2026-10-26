import Constants from 'expo-constants';
import { Platform } from 'react-native';

const API_PORT = 8000;

/**
 * API adresi. EXPO_PUBLIC_API_URL verilmişse o kullanılır; yoksa web'de localhost'a,
 * Expo Go'da ise Metro'yu çalıştıran geliştirme makinesine gidilir.
 */
export function resolveApiBaseUrl(): string {
  const fromEnv = process.env.EXPO_PUBLIC_API_URL;
  if (fromEnv) {
    return fromEnv.replace(/\/+$/, '');
  }
  if (Platform.OS !== 'web') {
    const host = Constants.expoConfig?.hostUri?.split(':')[0];
    if (host) {
      return `http://${host}:${API_PORT}`;
    }
  }
  return `http://localhost:${API_PORT}`;
}

export const API_BASE_URL = resolveApiBaseUrl();
