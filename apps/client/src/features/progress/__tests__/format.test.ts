import {
  formatDecimal,
  hintsCaption,
  independenceCaption,
  meterLabel,
  meterRatio,
} from '@/features/progress/format';

describe('ebeveyn özeti biçimlendirme', () => {
  it('ondalığı Türkçe virgülle yazar, boş değere tire koyar', () => {
    expect(formatDecimal(1.5)).toBe('1,5');
    expect(formatDecimal(2)).toBe('2');
    expect(formatDecimal(null)).toBe('–');
  });

  it('bağımsızlık cümlesini duruma göre kurar', () => {
    expect(independenceCaption(0, 0)).toBe('Bu dönemde çözülen soru yok');
    expect(independenceCaption(3, 3)).toBe('Hepsini ipucu almadan çözdü');
    expect(independenceCaption(3, 0)).toBe('Hepsinde ipucundan yararlandı');
    expect(independenceCaption(4, 1)).toBe('4 sorunun 1 tanesini ipucusuz çözdü');
  });

  it('ipucu açıklaması boş ve sıfır durumlarını ayırır', () => {
    expect(hintsCaption(null)).toBe('Henüz çözülen soru yok');
    expect(hintsCaption(0)).toBe('İpucu kullanmadı');
  });

  it('meter oranı 0–1 arasında kalır ve ekran okuyucu metni üretir', () => {
    expect(meterRatio(2, 4)).toBe(0.5);
    expect(meterRatio(3, 0)).toBe(0);
    expect(meterRatio(5, 4)).toBe(1);
    expect(meterLabel('kesirler', 2, 3)).toBe('kesirler: 3 sorudan 2 tanesi çözüldü');
  });
});
