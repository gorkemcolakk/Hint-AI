import { useSyncExternalStore } from 'react';

/** Yetişkin hesapları (ebeveyn, öğretmen) yenileme token'ı taşır; çocuk oturumu taşımaz. */
export type AdultKind = 'guardian' | 'teacher';
export type AdultSession = { kind: AdultKind; accessToken: string; refreshToken: string };
export type Session = AdultSession | { kind: 'child'; accessToken: string };

export function isAdultSession(session: Session | null): session is AdultSession {
  return session !== null && session.kind !== 'child';
}

export type SessionState = { status: 'loading' } | { status: 'ready'; session: Session | null };

let state: SessionState = { status: 'loading' };
const listeners = new Set<() => void>();

export function getSessionState(): SessionState {
  return state;
}

export function currentSession(): Session | null {
  return state.status === 'ready' ? state.session : null;
}

export function setSession(session: Session | null): void {
  state = { status: 'ready', session };
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Oturum durumunu izler; oturum değiştiğinde bileşen yeniden çizilir. */
export function useSessionState(): SessionState {
  return useSyncExternalStore(subscribe, getSessionState, getSessionState);
}

export function useSession(): Session | null {
  const current = useSessionState();
  return current.status === 'ready' ? current.session : null;
}
