import { ApiError, errorMessage } from '@/api/errors';
import type { components } from '@/api/schema';
import { getAccessToken } from '@/auth/auth';
import { API_BASE_URL } from '@/config';

export type HintResponse = components['schemas']['HintResponse'];
export type HintOut = components['schemas']['HintOut'];

const NETWORK_ERROR = 'Sunucuya ulaşılamadı. Bağlantını kontrol edip tekrar dene.';

export type StreamHintOptions = {
  problemId: string;
  message: string | null;
  onPartialText?: (partial: string) => void;
};

/**
 * SSE metin akışından (`event:` + `data:`) son ipucu yanıtını ve parçalı metni çözer.
 * Bölüm 9.2 olay şemasını (`event: hint` / `event: delta`) destekler.
 */
export function parseSseEvents(
  chunkText: string,
  onPartial?: (delta: string) => void,
): HintResponse | null {
  let finalResponse: HintResponse | null = null;
  let accumulated = '';
  const blocks = chunkText.split(/\r?\n\r?\n/);

  for (const block of blocks) {
    if (!block.trim()) continue;
    let eventName = 'message';
    const dataLines: string[] = [];

    for (const line of block.split(/\r?\n/)) {
      if (line.startsWith('event:')) {
        eventName = line.slice(6).trim();
      } else if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trim());
      }
    }
    if (dataLines.length === 0) continue;
    const rawData = dataLines.join('\n');

    try {
      const parsed = JSON.parse(rawData) as Record<string, unknown>;
      if (eventName === 'delta' || eventName === 'token') {
        const piece = typeof parsed.text === 'string' ? parsed.text : '';
        if (piece) {
          accumulated += piece;
          onPartial?.(accumulated);
        }
      } else if (eventName === 'hint' || 'can_request_next' in parsed) {
        if ('hint' in parsed) {
          finalResponse = parsed as unknown as HintResponse;
        } else if ('hint_id' in parsed && typeof parsed.text === 'string') {
          // Bölüm 9.2 doğrudan şema uyumluluğu
          finalResponse = {
            hint: {
              id: String(parsed.hint_id),
              level: Number(parsed.level ?? 0),
              level_name: String(parsed.level_name ?? `İpucu ${(Number(parsed.level ?? 0)) + 1}`),
              text: parsed.text,
            },
            can_request_next: Boolean(parsed.can_request_next),
            notice: typeof parsed.notice === 'string' ? parsed.notice : null,
            safety: null,
          };
        }
      }
    } catch {
      // Tamamlanmamış blok bir sonraki okumada birleştirilir.
    }
  }
  return finalResponse;
}

/**
 * İpucu ister: sunucu `text/event-stream` dönerse SSE akışını okur,
 * `application/json` dönerse mevcut JSON sözleşmesiyle kesintisiz çalışır.
 */
export async function requestHintWithStream({
  problemId,
  message,
  onPartialText,
}: StreamHintOptions): Promise<HintResponse> {
  const token = await getAccessToken();
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/v1/problems/${problemId}/hints`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream, application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message }),
    });
  } catch {
    throw new ApiError(NETWORK_ERROR, 0);
  }

  if (!response.ok) {
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }
    throw new ApiError(errorMessage(body), response.status);
  }

  const contentType = response.headers.get('content-type') ?? '';
  if (!contentType.includes('text/event-stream')) {
    return (await response.json()) as HintResponse;
  }

  if (response.body && typeof response.body.getReader === 'function') {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let latestPartial = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parsed = parseSseEvents(buffer, (partial) => {
        if (partial !== latestPartial) {
          latestPartial = partial;
          onPartialText?.(partial);
        }
      });
      if (parsed) return parsed;
    }
    buffer += decoder.decode();
    const finalParsed = parseSseEvents(buffer, onPartialText);
    if (finalParsed) return finalParsed;
  } else {
    const text = await response.text();
    const parsed = parseSseEvents(text, onPartialText);
    if (parsed) return parsed;
  }

  throw new ApiError('İpucu akışı okunamadı. Lütfen tekrar dene.', 502);
}

/**
 * İpucu faydalı mı geri bildirimi (Bölüm 9.1: POST /v1/hints/{id}/feedback).
 * Backend ucu henüz yoksa yerel durumu koruyarak sessizce tamamlanır.
 */
export async function submitHintFeedback(
  hintId: string,
  helpful: boolean,
): Promise<{ persisted: boolean }> {
  const token = await getAccessToken();
  try {
    const response = await fetch(`${API_BASE_URL}/v1/hints/${hintId}/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ helpful }),
    });
    if (response.ok) return { persisted: true };
    if (response.status === 404 || response.status === 405) return { persisted: false };
    return { persisted: false };
  } catch {
    return { persisted: false };
  }
}
