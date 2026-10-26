export type ConsentPurpose = 'service' | 'llm_processing' | 'photo_processing' | 'analytics';

export const CONSENT_OPTIONS: readonly {
  purpose: ConsentPurpose;
  label: string;
  description: string;
}[] = [
  {
    purpose: 'service',
    label: 'Hizmet (zorunlu)',
    description: 'Çocuk profilinin oluşturulması ve uygulamanın çalışması için gerekli.',
  },
  {
    purpose: 'llm_processing',
    label: 'Yapay zekâ ile işleme',
    description:
      'Sorular, kişisel bilgiler maskelendikten sonra yapay zekâ sağlayıcısına gönderilir. İpucu almak için gerekir.',
  },
  {
    purpose: 'photo_processing',
    label: 'Fotoğraf işleme',
    description: 'Soru fotoğraflarının metne çevrilmesi.',
  },
  {
    purpose: 'analytics',
    label: 'Analitik',
    description: 'Anonim kullanım istatistikleri.',
  },
];

export type NewChildForm = {
  nickname: string;
  birthYear: string;
  grade: string;
  purposes: ConsentPurpose[];
};

export type NewChildPayload = {
  nickname: string;
  birth_year: number;
  grade: number;
  purposes: ConsentPurpose[];
};

/** Formu doğrular; geçerliyse API'ye gidecek gövdeyi, değilse ilk hatayı döner. */
export function validateNewChild(
  form: NewChildForm,
  currentYear: number,
): { ok: true; payload: NewChildPayload } | { ok: false; error: string } {
  const nickname = form.nickname.trim();
  if (!nickname) {
    return { ok: false, error: 'Takma ad gerekli.' };
  }
  const birthYear = Number(form.birthYear.trim());
  const age = currentYear - birthYear;
  if (!/^\d{4}$/.test(form.birthYear.trim()) || age < 7 || age > 17) {
    return { ok: false, error: 'Hint.ai 7–17 yaş içindir; doğum yılını kontrol et.' };
  }
  const grade = Number(form.grade.trim());
  if (!Number.isInteger(grade) || grade < 1 || grade > 12) {
    return { ok: false, error: 'Sınıf 1 ile 12 arasında olmalı.' };
  }
  if (!form.purposes.includes('service')) {
    return { ok: false, error: 'Devam etmek için hizmet rızası gerekli.' };
  }
  return {
    ok: true,
    payload: { nickname, birth_year: birthYear, grade, purposes: form.purposes },
  };
}
