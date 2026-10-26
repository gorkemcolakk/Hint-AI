import { ApiError, unwrap } from '@/api/errors';
import { publicApi } from '@/api/public-client';

import { tokenExpiresAt } from './jwt';
import { currentSession, setSession, type Session } from './session-store';
import { clearStoredSession, loadStoredSession, saveSession } from './token-storage';

// Ebeveyn token'ının bitmesine bu kadar kala yenilenir.
const REFRESH_MARGIN_MS = 60_000;

type RefreshResult =
  | { status: 'ok'; session: Session }
  | { status: 'invalid' }
  | { status: 'unreachable' };

let refreshInFlight: Promise<string | null> | null = null;

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
    return {
      status: 'ok',
      session: {
        kind: 'guardian',
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
      },
    };
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
    if (stored?.kind === 'guardian') {
      const result = await requestRefresh(stored.refreshToken);
      if (result.status === 'ok') {
        await activate(result.session);
      } else if (result.status === 'invalid') {
        await activate(null);
      } else {
        // Sunucuya şu an ulaşılamıyor; oturum korunur, ilk istekte yeniden denenir.
        setSession({ kind: 'guardian', accessToken: '', refreshToken: stored.refreshToken });
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
  await activate({
    kind: 'guardian',
    accessToken: tokens.access_token,
    refreshToken: tokens.refresh_token,
  });
}

export async function register(input: {
  email: string;
  password: string;
  fullName?: string;
}): Promise<void> {
  await unwrap(
    publicApi.POST('/v1/auth/register', {
      body: {
        email: input.email,
        password: input.password,
        role: 'guardian',
        full_name: input.fullName || null,
      },
    }),
  );
  await signIn(input.email, input.password);
}

export async function signOut(): Promise<void> {
  const session = currentSession();
  if (session?.kind === 'guardian') {
    await revokeQuietly(session.refreshToken);
  }
  await activate(null);
}

/** Bu cihazı çocuk moduna geçirir; cihazdaki ebeveyn oturumu varsa kapatılır. */
export async function pairDevice(childId: string, code: string): Promise<void> {
  const result = await unwrap(
    publicApi.POST('/v1/auth/child-pair', { body: { child_id: childId, code } }),
  );
  const previous = currentSession();
  if (previous?.kind === 'guardian') {
    await revokeQuietly(previous.refreshToken);
  }
  await activate({ kind: 'child', accessToken: result.access_token });
}

async function refreshGuardian(refreshToken: string): Promise<string | null> {
  const result = await requestRefresh(refreshToken);
  if (currentSession()?.kind !== 'guardian') {
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

/** İsteklerde kullanılacak token; ebeveyn token'ı bitmek üzereyse önce yenilenir. */
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
  refreshInFlight ??= refreshGuardian(session.refreshToken).finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}
