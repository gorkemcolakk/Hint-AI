import { ApiError, unwrap } from '@/api/errors';
import { publicApi } from '@/api/public-client';
import { API_BASE_URL } from '@/config';

import { tokenExpiresAt, tokenRole } from './jwt';
import {
  type AdultKind,
  type AdultSession,
  currentSession,
  isAdultSession,
  setSession,
  type Session,
} from './session-store';
import { clearStoredSession, loadStoredSession, saveSession } from './token-storage';

// Yetişkin (ebeveyn/öğretmen) token'ının bitmesine bu kadar kala yenilenir.
const REFRESH_MARGIN_MS = 60_000;

type RefreshResult =
  { status: 'ok'; session: AdultSession } | { status: 'invalid' } | { status: 'unreachable' };

let refreshInFlight: Promise<string | null> | null = null;

/** Hesap türü token'daki rolden okunur (yönlendirme için; yetki sunucuda kontrol edilir). */
function adultSession(tokens: { access_token: string; refresh_token: string }): AdultSession {
  const kind: AdultKind = tokenRole(tokens.access_token) === 'teacher' ? 'teacher' : 'guardian';
  return { kind, accessToken: tokens.access_token, refreshToken: tokens.refresh_token };
}

async function activate(session: Session | null): Promise<void> {
  if (session) {
    await saveSession(session);
  } else {
    await clearStoredSession();
  }
  setSession(session);
}

async function requestRefresh(refreshToken: string): Promise<RefreshResult> {
  try {
    const tokens = await unwrap(
      publicApi.POST('/v1/auth/refresh', { body: { refresh_token: refreshToken } }),
    );
    return { status: 'ok', session: adultSession(tokens) };
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return { status: 'invalid' };
    }
    return { status: 'unreachable' };
  }
}

async function revokeQuietly(refreshToken: string): Promise<void> {
  try {
    await unwrap(publicApi.POST('/v1/auth/logout', { body: { refresh_token: refreshToken } }));
  } catch {
    // Sunucuya ulaşılamasa da yerel oturum kapatılır; token süresi dolunca zaten geçersiz olur.
  }
}

/** Uygulama açılışında cihazda saklanan oturumu geri yükler. */
export async function restoreSession(): Promise<void> {
  try {
    const stored = await loadStoredSession();
    if (stored?.kind === 'child') {
      setSession({ kind: 'child', accessToken: stored.accessToken });
      return;
    }
    if (stored) {
      const result = await requestRefresh(stored.refreshToken);
      if (result.status === 'ok') {
        await activate(result.session);
      } else if (result.status === 'invalid') {
        await activate(null);
      } else {
        // Sunucuya şu an ulaşılamıyor; oturum korunur, ilk istekte yeniden denenir.
        setSession({ kind: stored.kind, accessToken: '', refreshToken: stored.refreshToken });
      }
      return;
    }
    setSession(null);
  } catch {
    setSession(null);
  }
}

export async function signIn(email: string, password: string): Promise<void> {
  const tokens = await unwrap(publicApi.POST('/v1/auth/login', { body: { email, password } }));
  await activate(adultSession(tokens));
}

export async function register(input: {
  email: string;
  password: string;
  fullName?: string;
  role?: AdultKind;
}): Promise<void> {
  await unwrap(
    publicApi.POST('/v1/auth/register', {
      body: {
        email: input.email,
        password: input.password,
        role: input.role ?? 'guardian',
        full_name: input.fullName || null,
      },
    }),
  );
  await signIn(input.email, input.password);
}

export async function signOut(): Promise<void> {
  const session = currentSession();
  if (isAdultSession(session)) {
    await revokeQuietly(session.refreshToken);
  }
  await activate(null);
}

/** Bu cihazı çocuk moduna geçirir; cihazdaki yetişkin oturumu varsa kapatılır. */
export async function pairDevice(childId: string, code: string): Promise<void> {
  const result = await unwrap(
    publicApi.POST('/v1/auth/child-pair', { body: { child_id: childId, code } }),
  );
  const previous = currentSession();
  if (isAdultSession(previous)) {
    await revokeQuietly(previous.refreshToken);
  }
  await activate({ kind: 'child', accessToken: result.access_token });
}

const DEV_SHORTCUTS_OFF =
  'Demo kısayolu kapalı. apps/api/.env içinde HINT_DEV_SHORTCUTS=true olmalı ve API yeniden başlatılmalı.';

async function devToken<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { method: 'POST' });
  } catch {
    throw new ApiError('Sunucuya ulaşılamadı. API açık mı?', 0);
  }
  if (response.status === 404) {
    throw new ApiError(DEV_SHORTCUTS_OFF, 404);
  }
  if (!response.ok) {
    throw new ApiError('Demo oturumu açılamadı.', response.status);
  }
  return (await response.json()) as T;
}

/**
 * Yalnızca yerel deneme (__DEV__): eşleştirme bağlantısı olmadan demo çocuk oturumu açar.
 * Sunucu tarafı HINT_DEV_SHORTCUTS=true değilse uç nokta yoktur.
 */
export async function devSignInAsChild(): Promise<void> {
  const result = await devToken<{ access_token: string }>('/v1/dev/demo-child');
  await activate({ kind: 'child', accessToken: result.access_token });
}

/** Yalnızca yerel deneme (__DEV__): demo ebeveyn oturumu açar. */
export async function devSignInAsGuardian(): Promise<void> {
  await activate(
    adultSession(
      await devToken<{ access_token: string; refresh_token: string }>('/v1/dev/demo-guardian'),
    ),
  );
}

/** Yalnızca yerel deneme (__DEV__): demo öğretmen oturumu açar (demo sınıfı hazırlanır). */
export async function devSignInAsTeacher(): Promise<void> {
  await activate(
    adultSession(
      await devToken<{ access_token: string; refresh_token: string }>('/v1/dev/demo-teacher'),
    ),
  );
}

async function refreshAdult(refreshToken: string): Promise<string | null> {
  const result = await requestRefresh(refreshToken);
  if (!isAdultSession(currentSession())) {
    // Yenileme sürerken oturum kapatıldı ya da değişti.
    return null;
  }
  if (result.status === 'ok') {
    await activate(result.session);
    return result.session.accessToken;
  }
  if (result.status === 'invalid') {
    await activate(null);
  }
  return null;
}

/** İsteklerde kullanılacak token; yetişkin token'ı bitmek üzereyse önce yenilenir. */
export async function getAccessToken(): Promise<string | null> {
  const session = currentSession();
  if (!session) {
    return null;
  }
  if (session.kind === 'child') {
    return session.accessToken;
  }
  const expiresAt = tokenExpiresAt(session.accessToken);
  if (expiresAt !== null && expiresAt - Date.now() > REFRESH_MARGIN_MS) {
    return session.accessToken;
  }
  // Aynı anda gelen istekler tek yenileme çağrısını paylaşır: refresh token rotasyonlu olduğu
  // için ikinci bir çağrı eski token'la reddedilir ve oturumu kapatırdı.
  refreshInFlight ??= refreshAdult(session.refreshToken).finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}
