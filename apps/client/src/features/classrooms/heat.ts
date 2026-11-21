/**
 * Kazanım ısı haritası skalası: ortalama ipucu (0–5) → tek tonlu, açıktan koyuya 5 basamak
 * (dataviz: sıralı = tek renk tonu). Metin kontrastı hesaplandı: ilk üç basamakta koyu metin
 * (≥ 7,7:1), son ikisinde beyaz metin (≥ 6,2:1).
 */
export const HEAT_STEPS = [
  { color: '#F3EEF8', text: '#1B1B1F' },
  { color: '#DCCDEB', text: '#1B1B1F' },
  { color: '#BFA3DA', text: '#1B1B1F' },
  { color: '#7A4AAB', text: '#FFFFFF' },
  { color: '#4E2373', text: '#FFFFFF' },
] as const;

export const HEAT_LEGEND = ['0–1', '1–2', '2–3', '3–4', '4+'] as const;

export function heatStep(avgHints: number): (typeof HEAT_STEPS)[number] {
  const index = Math.min(HEAT_STEPS.length - 1, Math.max(0, Math.floor(avgHints)));
  return HEAT_STEPS[index];
}

export function cellLabel(
  topic: string,
  nickname: string,
  cell: { problems: number; solved: number; avg_hints: number } | undefined,
): string {
  if (!cell) return `${nickname}, ${topic}: bu konuda soru yok`;
  return `${nickname}, ${topic}: ${cell.problems} soru, ${cell.solved} çözüldü, ortalama ${cell.avg_hints
    .toLocaleString('tr-TR')
    .replace('.', ',')} ipucu`;
}

export function struggleCaption(topic: {
  students: number;
  struggling: number;
  avg_hints: number | null;
}): string {
  const avg =
    topic.avg_hints === null
      ? ''
      : ` · ort. ${topic.avg_hints.toLocaleString('tr-TR', { maximumFractionDigits: 1 })} ipucu`;
  if (topic.struggling === 0) return `${topic.students} öğrenci, zorlanan yok${avg}`;
  return `${topic.students} öğrenciden ${topic.struggling} tanesi zorlanıyor${avg}`;
}

/** Davet kodunu okunaklı gösterir: 6 karakterli kod 3+3 gruplanır ("DEMO6A" → "DEM O6A"). */
export function formatJoinCode(code: string): string {
  return code.length === 6 ? `${code.slice(0, 3)} ${code.slice(3)}` : code;
}
