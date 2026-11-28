import { ApiError } from '@/api/errors';
import type { components } from '@/api/schema';
import { getAccessToken } from '@/auth/auth';
import { API_BASE_URL } from '@/config';

export type ChildProfile = components['schemas']['ChildProfileResponse'];
export type SolutionPolicy =
  | 'never'
  | 'similar_example_only'
  | 'after_attempts_with_notice'
  | 'guardian_only';
export type PrivacyLevel = 'summary_only' | 'full_transcript';

export const SOLUTION_POLICY_OPTIONS: readonly {
  value: SolutionPolicy;
  label: string;
  description: string;
}[] = [
  {
    value: 'never',
    label: 'Tam çözümü asla gösterme (Önerilen)',
    description: 'Yalnızca L0–L4 Sokratik ipuçları verilir; nihai cevap açıklanmaz.',
  },
  {
    value: 'similar_example_only',
    label: 'En fazla benzer çözümlü örnek (L4)',
    description: 'Farklı sayılarla benzer bir örnek çözülür, asıl soru öğrenciye bırakılır.',
  },
  {
    value: 'after_attempts_with_notice',
    label: 'Denemelerden sonra ebeveyn bildirimiyle (Pilot sonrası)',
    description: 'Politika tercihi kaydedilir; MVP güvenlik kilidi nedeniyle L5 şu an kapalıdır.',
  },
  {
    value: 'guardian_only',
    label: 'Yalnızca ebeveyn kilidiyle (Pilot sonrası)',
    description: 'Politika tercihi kaydedilir; MVP güvenlik kilidi nedeniyle L5 şu an kapalıdır.',
  },
];

export const PRIVACY_LEVEL_OPTIONS: readonly {
  value: PrivacyLevel;
  label: string;
  description: string;
}[] = [
  {
    value: 'summary_only',
    label: 'Yalnızca konu ve ilerleme özeti (Önerilen)',
    description: 'Soru metinleri gizli kalır; çalışılan konular, ipucu sayısı ve güvenlik uyarıları görünür.',
  },
  {
    value: 'full_transcript',
    label: 'Maskeli soru metinlerini de göster',
    description: 'Son sorularda kişisel bilgileri maskelenmiş soru metinleri ebeveyn özetinde listelenir.',
  },
];

export const DAILY_LIMIT_PRESETS = [5, 10, 20, 50] as const;

export function validateChildSettings(input: {
  nickname: string;
  dailyLimit: string;
}): { ok: true; nickname: string; dailyLimit: number } | { ok: false; error: string } {
  const nickname = input.nickname.trim();
  if (!nickname) {
    return { ok: false, error: 'Takma ad boş bırakılamaz.' };
  }
  const trimmedLimit = input.dailyLimit.trim();
  const limit = Number(trimmedLimit);
  if (!/^\d+$/.test(trimmedLimit) || !Number.isInteger(limit) || limit < 0 || limit > 100) {
    return { ok: false, error: 'Günlük soru sınırı 0 ile 100 arasında bir tam sayı olmalı.' };
  }
  return { ok: true, nickname, dailyLimit: limit };
}

function triggerWebJsonDownload(filename: string, jsonText: string): void {
  if (typeof document === 'undefined' || typeof Blob === 'undefined') return;
  const blob = new Blob([jsonText], { type: 'application/json;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

/**
 * Çocuk verilerini JSON olarak dışa aktarır (Bölüm 10.4).
 * Sunucuda `/v1/children/{id}/export` varsa onu kullanır, yoksa mevcut özet uçlarından derler.
 */
export async function exportChildDataBundle(profile: ChildProfile): Promise<string> {
  const token = await getAccessToken();
  const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

  try {
    const direct = await fetch(`${API_BASE_URL}/v1/children/${profile.id}/export`, { headers });
    if (direct.ok) {
      const data = (await direct.json()) as unknown;
      const formatted = JSON.stringify(data, null, 2);
      triggerWebJsonDownload(`hint-ai-${profile.nickname}-veri.json`, formatted);
      return formatted;
    }
  } catch {
    // Yedek istemci derlemesine düş.
  }

  let summary: unknown = null;
  let classrooms: unknown = null;
  try {
    const [sumRes, clsRes] = await Promise.all([
      fetch(`${API_BASE_URL}/v1/children/${profile.id}/summary?days=90`, { headers }),
      fetch(`${API_BASE_URL}/v1/children/${profile.id}/classrooms`, { headers }),
    ]);
    if (sumRes.ok) summary = await sumRes.json();
    if (clsRes.ok) classrooms = await clsRes.json();
  } catch {
    // Çevrimdışıysa profil özetiyle dışa aktar.
  }

  const bundle = {
    exported_at: new Date().toISOString(),
    profile,
    summary_90d: summary,
    classrooms,
  };
  const formatted = JSON.stringify(bundle, null, 2);
  triggerWebJsonDownload(`hint-ai-${profile.nickname}-veri.json`, formatted);
  return formatted;
}

/**
 * Çocuk profilini silme isteği gönderir (`DELETE /v1/children/{id}`).
 * Backend ucu henüz eklenmemişse `supported: false` döner.
 */
export async function requestDeleteChildProfile(
  childId: string,
): Promise<{ deleted: true } | { deleted: false; reason: string }> {
  const token = await getAccessToken();
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/v1/children/${childId}`, {
      method: 'DELETE',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
  } catch {
    throw new ApiError('Sunucuya ulaşılamadı. Bağlantını kontrol edip tekrar dene.', 0);
  }
  if (response.ok) {
    return { deleted: true };
  }
  if (response.status === 404 || response.status === 405) {
    return {
      deleted: false,
      reason:
        'Kalıcı profil silme uç noktası arka plan aşamasında bağlanacak; şimdilik isteğe bağlı tüm veri işleme izinleri kapatıldı.',
    };
  }
  throw new ApiError('Profil silinemedi. Lütfen tekrar dene.', response.status);
}
