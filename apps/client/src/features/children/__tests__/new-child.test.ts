import { validateNewChild, type NewChildForm } from '@/features/children/new-child';

const CURRENT_YEAR = 2026;

function form(overrides: Partial<NewChildForm> = {}): NewChildForm {
  return {
    nickname: 'Deniz',
    birthYear: '2015',
    grade: '6',
    purposes: ['service'],
    ...overrides,
  };
}

describe('validateNewChild', () => {
  it('geçerli formu API gövdesine çevirir', () => {
    expect(validateNewChild(form({ nickname: '  Deniz  ' }), CURRENT_YEAR)).toEqual({
      ok: true,
      payload: { nickname: 'Deniz', birth_year: 2015, grade: 6, purposes: ['service'] },
    });
  });

  it('hizmet rızası olmadan profil oluşturulmaz', () => {
    expect(validateNewChild(form({ purposes: ['analytics'] }), CURRENT_YEAR)).toEqual({
      ok: false,
      error: 'Devam etmek için hizmet rızası gerekli.',
    });
  });

  it.each(['2020', '2008', '15', 'abcd', ''])('7–17 yaş dışındaki doğum yılını reddeder: %p', (birthYear) => {
    expect(validateNewChild(form({ birthYear }), CURRENT_YEAR).ok).toBe(false);
  });

  it.each(['0', '13', '6.5', ''])('geçersiz sınıfı reddeder: %p', (grade) => {
    expect(validateNewChild(form({ grade }), CURRENT_YEAR).ok).toBe(false);
  });

  it('boş takma adı reddeder', () => {
    expect(validateNewChild(form({ nickname: '   ' }), CURRENT_YEAR).ok).toBe(false);
  });
});
