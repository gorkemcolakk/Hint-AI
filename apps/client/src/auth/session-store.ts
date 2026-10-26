import { useSyncExternalStore } from 'react';

export type Session =
  | { kind: 'guardian'; accessToken: string; refreshToken: string }
  | { kind: 'child'; accessToken: string };

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
