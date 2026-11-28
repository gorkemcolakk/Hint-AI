import { parsePairingInput } from '@/features/children/pairing-input';
import { validateChildSettings } from '@/features/children/settings-logic';

const SAMPLE_UUID = '123e4567-e89b-12d3-a456-426614174000';

describe('parsePairingInput', () => {
  it('web veya derin bağlantı URL parametrelerini ayrıştırır', () => {
    const res = parsePairingInput(
      `http://localhost:8081/pair?child=${SAMPLE_UUID}&code=654321`,
    );
    expect(res).toEqual({ ok: true, childId: SAMPLE_UUID, code: '654321' });
  });

  it('serbest metin içindeki UUID ve 6 haneli kodu yakalar', () => {
    const res = parsePairingInput(`${SAMPLE_UUID}:908172`);
    expect(res).toEqual({ ok: true, childId: SAMPLE_UUID, code: '908172' });
  });

  it('yalnızca 6 haneli kod verildiğinde açıklayıcı uyarı döner', () => {
    const res = parsePairingInput('123456');
    expect(res.ok).toBe(false);
    if (!res.ok) {
      expect(res.error).toContain('tam eşleştirme bağlantısını');
    }
  });
});

describe('validateChildSettings', () => {
  it('geçerli takma ad ve günlük sınırı kabul eder', () => {
    expect(validateChildSettings({ nickname: '  Deniz ', dailyLimit: '15' })).toEqual({
      ok: true,
      nickname: 'Deniz',
      dailyLimit: 15,
    });
  });

  it('boş takma ad veya aralık dışı sınırı reddeder', () => {
    expect(validateChildSettings({ nickname: '   ', dailyLimit: '10' }).ok).toBe(false);
    expect(validateChildSettings({ nickname: 'Deniz', dailyLimit: '150' }).ok).toBe(false);
    expect(validateChildSettings({ nickname: 'Deniz', dailyLimit: '-1' }).ok).toBe(false);
  });
});
