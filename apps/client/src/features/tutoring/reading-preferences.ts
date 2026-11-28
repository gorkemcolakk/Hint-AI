import { useSyncExternalStore } from 'react';

export type RecentProblemEntry = {
  id: string;
  preview: string;
  topic?: string | null;
  solved: boolean;
  updatedAt: number;
};

type ChildUiState = {
  /** Disleksi/rahat okuma modu: artırılmış harf ve satır aralığı + büyütülmüş yazı (Bölüm 5.4). */
  comfortableReading: boolean;
  /** Son çalışılan sorunun hafif önbelleği (Bölüm 5.4). */
  recentProblem: RecentProblemEntry | null;
  /** Oturum başlangıcı; uzun çalışmada nazik mola hatırlatması için (Bölüm 10.2). */
  sessionStartedAt: number;
  breakDismissed: boolean;
};

let state: ChildUiState = {
  comfortableReading: false,
  recentProblem: null,
  sessionStartedAt: Date.now(),
  breakDismissed: false,
};

const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getSnapshot(): ChildUiState {
  return state;
}

export function setComfortableReading(enabled: boolean): void {
  state = { ...state, comfortableReading: enabled };
  emit();
}

export function rememberRecentProblem(entry: Omit<RecentProblemEntry, 'updatedAt'>): void {
  state = {
    ...state,
    recentProblem: { ...entry, updatedAt: Date.now() },
  };
  emit();
}

export function dismissBreakReminder(): void {
  state = { ...state, breakDismissed: true };
  emit();
}

export function resetChildUiState(): void {
  state = {
    comfortableReading: state.comfortableReading,
    recentProblem: null,
    sessionStartedAt: Date.now(),
    breakDismissed: false,
  };
  emit();
}

export function useChildUiState(): ChildUiState {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}

/** 30 dakikayı aşan kesintisiz çalışmada nazik mola önerisi (Bölüm 10.2). */
export const STUDY_BREAK_REMINDER_MS = 30 * 60 * 1000;

export function shouldSuggestBreak(now: number, current: ChildUiState = state): boolean {
  if (current.breakDismissed) return false;
  return now - current.sessionStartedAt >= STUDY_BREAK_REMINDER_MS;
}
