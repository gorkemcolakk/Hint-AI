import {
  hintButtonLabel,
  ladderCaption,
  ladderSteps,
  themeForAgeBand,
} from '@/features/tutoring/ladder';

describe('ipucu merdiveni yardımcıları', () => {
  it('henüz ipucu yokken tüm basamaklar sırada bekler', () => {
    expect(ladderSteps(null, 4)).toEqual([
      'upcoming',
      'upcoming',
      'upcoming',
      'upcoming',
      'upcoming',
    ]);
  });

  it('geçilen, mevcut ve sıradaki basamakları ayırır', () => {
    expect(ladderSteps(2, 4)).toEqual(['done', 'done', 'current', 'upcoming', 'upcoming']);
  });

  it('düşük güvenli soruda merdiven kısalır', () => {
    expect(ladderSteps(0, 2)).toHaveLength(3);
  });

  it('düğme etiketi ilk ipucundan sonra "takıldım" olur', () => {
    expect(hintButtonLabel(0)).toBe('Bir ipucu ver');
    expect(hintButtonLabel(1)).toBe('Takıldım, bir ipucu daha');
  });

  it('basamak açıklaması 1 tabanlıdır', () => {
    expect(ladderCaption(null, 4)).toContain('Henüz ipucu almadın');
    expect(ladderCaption(1, 4)).toBe('İpucu basamağı 2 / 5');
  });

  it('14-17 yaş Odak, diğerleri Keşif temasını alır', () => {
    expect(themeForAgeBand('14-17').name).toBe('odak');
    expect(themeForAgeBand('11-13').name).toBe('kesif');
    expect(themeForAgeBand(undefined).name).toBe('kesif');
  });
});
