const UUID_PATTERN = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;
const SIX_DIGIT_PATTERN = /\b(\d{6})\b/;

export type ParsedPairing =
  | { ok: true; childId: string; code: string }
  | { ok: false; error: string };

/**
 * Ebeveyn panelinden kopyalanan eşleştirme bağlantısını (`.../pair?child=...&code=123456`)
 * veya `<child_uuid>:<6_haneli_kod>` biçimindeki anahtarı ayrıştırır.
 */
export function parsePairingInput(rawLinkOrToken: string, separateCode = ''): ParsedPairing {
  const input = rawLinkOrToken.trim();
  const extraCode = separateCode.trim();

  if (!input && !extraCode) {
    return { ok: false, error: 'Ebeveyn panelindeki eşleştirme bağlantısını buraya yapıştır.' };
  }

  // 1) URL sorgu parametrelerinden dene (?child=...&code=...)
  if (input.includes('child=') || input.includes('code=')) {
    const queryIndex = input.indexOf('?');
    const query = queryIndex >= 0 ? input.slice(queryIndex + 1) : input;
    const params = new URLSearchParams(query);
    const child = params.get('child')?.trim() ?? '';
    const code = (params.get('code') ?? extraCode).trim();
    if (UUID_PATTERN.test(child) && /^\d{6}$/.test(code)) {
      return { ok: true, childId: child, code };
    }
  }

  // 2) Serbest metin içinde UUID + 6 haneli kod ara (ör. Paylaş metni veya `uuid:123456`)
  const uuidMatch = UUID_PATTERN.exec(input);
  const withoutUuid = uuidMatch ? input.replace(uuidMatch[0], ' ') : input;
  const codeCandidate = extraCode || (SIX_DIGIT_PATTERN.exec(withoutUuid)?.[1] ?? '');

  if (uuidMatch && /^\d{6}$/.test(codeCandidate)) {
    return { ok: true, childId: uuidMatch[0], code: codeCandidate };
  }

  if (/^\d{6}$/.test(input) && !uuidMatch) {
    return {
      ok: false,
      error:
        'Yalnızca 6 haneli kod girildi; güvenlik için ebeveyn panelindeki tam eşleştirme bağlantısını yapıştır.',
    };
  }

  return {
    ok: false,
    error: 'Bağlantı eksik ya da hatalı görünüyor. Ebeveyn panelinden bağlantıyı kopyalayıp yapıştır.',
  };
}
