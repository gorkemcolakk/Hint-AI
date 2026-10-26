const NETWORK_ERROR = 'Sunucuya ulaşılamadı. Bağlantını kontrol edip tekrar dene.';
const GENERIC_ERROR = 'Bir şeyler ters gitti. Lütfen tekrar dene.';
const VALIDATION_ERROR = 'Girdiğin bilgileri kontrol edip tekrar dene.';

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/** FastAPI hata gövdesinden kullanıcıya gösterilecek mesajı çıkarır. */
export function errorMessage(body: unknown): string {
  if (typeof body === 'object' && body !== null && 'detail' in body) {
    const { detail } = body;
    if (typeof detail === 'string') {
      return detail;
    }
    if (Array.isArray(detail)) {
      // Pydantic doğrulama mesajları İngilizce; kullanıcıya genel bir mesaj gösterilir.
      return VALIDATION_ERROR;
    }
  }
  return GENERIC_ERROR;
}

type FetchResult<T> = { data?: T; error?: unknown; response: Response };

/** openapi-fetch sonucunu veriye çevirir; başarısız yanıtta ApiError fırlatır. */
export async function unwrap<T>(request: Promise<FetchResult<T>>): Promise<T> {
  let result: FetchResult<T>;
  try {
    result = await request;
  } catch {
    throw new ApiError(NETWORK_ERROR, 0);
  }
  if (!result.response.ok) {
    throw new ApiError(errorMessage(result.error), result.response.status);
  }
  return result.data as T;
}

export function describeError(error: unknown): string {
  return error instanceof ApiError ? error.message : GENERIC_ERROR;
}
