import { ApiError, describeError, errorMessage, unwrap } from '@/api/errors';

function response(status: number): Response {
  return { ok: status >= 200 && status < 300, status } as Response;
}

describe('errorMessage', () => {
  it('FastAPI detail metnini olduğu gibi gösterir', () => {
    expect(errorMessage({ detail: 'E-posta veya parola hatalı' })).toBe(
      'E-posta veya parola hatalı',
    );
  });

  it('doğrulama hata listesi için genel Türkçe mesaj döner', () => {
    expect(errorMessage({ detail: [{ msg: 'String should have at least 8 characters' }] })).toBe(
      'Girdiğin bilgileri kontrol edip tekrar dene.',
    );
  });

  it('tanınmayan gövdede genel mesaj döner', () => {
    expect(errorMessage(undefined)).toBe('Bir şeyler ters gitti. Lütfen tekrar dene.');
  });
});

describe('unwrap', () => {
  it('başarılı yanıtta veriyi döner', async () => {
    await expect(unwrap(Promise.resolve({ data: { id: 1 }, response: response(200) }))).resolves.toEqual({
      id: 1,
    });
  });

  it('başarısız yanıtta durum koduyla ApiError fırlatır', async () => {
    const result = unwrap(
      Promise.resolve({ error: { detail: 'Çocuk profili bulunamadı' }, response: response(404) }),
    );
    await expect(result).rejects.toEqual(new ApiError('Çocuk profili bulunamadı', 404));
    await expect(result).rejects.toMatchObject({ status: 404 });
  });

  it('ağ hatasını kullanıcıya anlaşılır mesajla bildirir', async () => {
    const error = await unwrap(Promise.reject(new TypeError('Failed to fetch'))).catch(
      (caught: unknown) => caught,
    );
    expect(error).toBeInstanceOf(ApiError);
    expect(describeError(error)).toBe('Sunucuya ulaşılamadı. Bağlantını kontrol edip tekrar dene.');
  });
});
