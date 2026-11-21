import {
  cellLabel,
  formatJoinCode,
  HEAT_STEPS,
  heatStep,
  struggleCaption,
} from '@/features/classrooms/heat';

describe('ısı haritası yardımcıları', () => {
  it('ortalama ipucunu 5 basamağa yerleştirir, uçları sınırlar', () => {
    expect(heatStep(0)).toBe(HEAT_STEPS[0]);
    expect(heatStep(1.5)).toBe(HEAT_STEPS[1]);
    expect(heatStep(3.9)).toBe(HEAT_STEPS[3]);
    expect(heatStep(5)).toBe(HEAT_STEPS[4]);
    expect(heatStep(-1)).toBe(HEAT_STEPS[0]);
  });

  it('koyu basamaklarda beyaz, açıklarda koyu metin kullanır', () => {
    expect(HEAT_STEPS.map((step) => step.text)).toEqual([
      '#1B1B1F',
      '#1B1B1F',
      '#1B1B1F',
      '#FFFFFF',
      '#FFFFFF',
    ]);
  });

  it('hücre için ekran okuyucu metni üretir', () => {
    expect(cellLabel('kesirler', 'Ali', undefined)).toBe('Ali, kesirler: bu konuda soru yok');
    expect(cellLabel('kesirler', 'Ali', { problems: 3, solved: 2, avg_hints: 1.5 })).toBe(
      'Ali, kesirler: 3 soru, 2 çözüldü, ortalama 1,5 ipucu',
    );
  });

  it('zorlanma açıklamasını kurar', () => {
    expect(struggleCaption({ students: 4, struggling: 0, avg_hints: 0.5 })).toBe(
      '4 öğrenci, zorlanan yok · ort. 0,5 ipucu',
    );
    expect(struggleCaption({ students: 4, struggling: 3, avg_hints: 3.2 })).toBe(
      '4 öğrenciden 3 tanesi zorlanıyor · ort. 3,2 ipucu',
    );
  });

  it('davet kodunu 3+3 gruplar', () => {
    expect(formatJoinCode('DEMO6A')).toBe('DEM O6A');
  });
});
