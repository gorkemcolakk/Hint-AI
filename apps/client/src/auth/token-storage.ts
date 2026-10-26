import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

import type { Session } from './session-store';

const STORAGE_KEY = 'hintai.session';

/** Cihazda saklanan oturum: ebeveyn için yalnızca yenileme token'ı, çocuk için kısa ömürlü token. */
export type StoredSession =
  | { kind: 'guardian'; refreshToken: string }
  | { kind: 'child'; accessToken: string };

// Web'de token'lar yalnızca bellekte tutulur (localStorage yok); sayfa yenilenince oturum kapanır.
let memoryValue: string | null = null;

async function read(): Promise<string | null> {
  return Platform.OS === 'web' ? memoryValue : SecureStore.getItemAsync(STORAGE_KEY);
}

async function write(value: string | null): Promise<void> {
  if (Platform.OS === 'web') {
    memoryValue = value;
  } else if (value === null) {
    await SecureStore.deleteItemAsync(STORAGE_KEY);
  } else {
    await SecureStore.setItemAsync(STORAGE_KEY, value);
  }
}

function isStoredSession(value: unknown): value is StoredSession {
  if (typeof value !== 'object' || value === null || !('kind' in value)) {
    return false;
  }
  if (value.kind === 'guardian') {
    return 'refreshToken' in value && typeof value.refreshToken === 'string';
  }
  if (value.kind === 'child') {
    return 'accessToken' in value && typeof value.accessToken === 'string';
  }
  return false;
}

export async function loadStoredSession(): Promise<StoredSession | null> {
  const raw = await read();
  if (!raw) {
    return null;
  }
  try {
    const value: unknown = JSON.parse(raw);
    return isStoredSession(value) ? value : null;
  } catch {
    return null;
  }
}

export async function saveSession(session: Session): Promise<void> {
  const stored: StoredSession =
    session.kind === 'guardian'
      ? { kind: 'guardian', refreshToken: session.refreshToken }
      : { kind: 'child', accessToken: session.accessToken };
  await write(JSON.stringify(stored));
}

export async function clearStoredSession(): Promise<void> {
  await write(null);
}
