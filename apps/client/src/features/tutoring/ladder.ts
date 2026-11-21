import { Colors } from '@/constants/theme';

/** Yaş bandına göre iki tema (Bölüm 5.7): Keşif (7–13) ve Odak (14–17). */
export type ChildTheme = {
  name: 'kesif' | 'odak';
  accent: string;
  accentSoft: string;
  fontScale: number;
  emoji: boolean;
};

const KESIF: ChildTheme = {
  name: 'kesif',
  accent: Colors.child,
  accentSoft: '#E6F4F1',
  fontScale: 1.1,
  emoji: true,
};

const ODAK: ChildTheme = {
  name: 'odak',
  accent: '#3730A3',
  accentSoft: '#EEF0FB',
  fontScale: 1,
  emoji: false,
};

export function themeForAgeBand(ageBand: string | undefined): ChildTheme {
  return ageBand === '14-17' ? ODAK : KESIF;
}

export type StepState = 'done' | 'current' | 'upcoming';

/** İpucu merdiveninin basamakları (L0..maxLevel) ve her birinin durumu. */
export function ladderSteps(current: number | null, maxLevel: number): StepState[] {
  return Array.from({ length: maxLevel + 1 }, (_, level) => {
    if (current === null || level > current) return 'upcoming';
    return level === current ? 'current' : 'done';
  });
}

export function hintButtonLabel(hintCount: number): string {
  return hintCount === 0 ? 'Bir ipucu ver' : 'Takıldım, bir ipucu daha';
}

export function ladderCaption(current: number | null, maxLevel: number): string {
  if (current === null) return 'Henüz ipucu almadın. Önce kendin denemek ister misin?';
  return `İpucu basamağı ${current + 1} / ${maxLevel + 1}`;
}

/** Zorlanma sinyali; sunucu bunu görünce önce destek verir ve bir basamak atlar. */
export const FRUSTRATION_MESSAGE = 'Bu çok zor, yapamıyorum.';
