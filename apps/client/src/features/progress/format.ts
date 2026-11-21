/** Ebeveyn özeti için biçimlendirme yardımcıları (Türkçe sayı ve tarih biçimi). */

export function formatDecimal(value: number | null | undefined): string {
  if (value === null || value === undefined) return '–';
  return value.toLocaleString('tr-TR', { maximumFractionDigits: 1 });
}

export function formatShortDate(iso: string): string {
  return new Date(iso).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' });
}

/** Bağımsızlık cümlesi: ipucusuz çözülen soruların çözülenlere oranı. */
export function independenceCaption(solved: number, withoutHints: number): string {
  if (solved === 0) return 'Bu dönemde çözülen soru yok';
  if (withoutHints === solved) return 'Hepsini ipucu almadan çözdü';
  if (withoutHints === 0) return 'Hepsinde ipucundan yararlandı';
  return `${solved} sorunun ${withoutHints} tanesini ipucusuz çözdü`;
}

export function hintsCaption(avg: number | null | undefined): string {
  if (avg === null || avg === undefined) return 'Henüz çözülen soru yok';
  if (avg === 0) return 'İpucu kullanmadı';
  return 'Çözülen soru başına; azaldıkça daha bağımsız';
}

/** Meter satırının ekran okuyucu metni. */
export function meterLabel(name: string, value: number, total: number): string {
  return `${name}: ${total} sorudan ${value} tanesi çözüldü`;
}

export function meterRatio(value: number, total: number): number {
  if (total <= 0) return 0;
  return Math.min(1, Math.max(0, value / total));
}
