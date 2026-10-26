import { getAccessToken, pairDevice, signOut } from '@/auth/auth';
import { currentSession, setSession } from '@/auth/session-store';

const mockPost = jest.fn();

jest.mock('@/api/public-client', () => ({
  publicApi: { POST: (...args: unknown[]) => mockPost(...args) },
}));

jest.mock('@/auth/token-storage', () => ({
  loadStoredSession: jest.fn(async () => null),
  saveSession: jest.fn(async () => undefined),
  clearStoredSession: jest.fn(async () => undefined),
}));

function tokenExpiringIn(seconds: number): string {
  const payload = btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + seconds }));
  return `header.${payload.replace(/=+$/, '')}.signature`;
}

function reply(status: number, body?: unknown) {
  const response = { ok: status >= 200 && status < 300, status } as Response;
  return response.ok ? { data: body, response } : { error: body, response };
}

beforeEach(() => {
  mockPost.mockReset();
  setSession(null);
});

describe('getAccessToken', () => {
  it('süresi dolmamış ebeveyn token’ını yenilemeden kullanır', async () => {
    const token = tokenExpiringIn(600);
    setSession({ kind: 'guardian', accessToken: token, refreshToken: 'r1' });

    await expect(getAccessToken()).resolves.toBe(token);
    expect(mockPost).not.toHaveBeenCalled();
  });

  it('eşzamanlı istekler tek bir yenileme çağrısını paylaşır', async () => {
    const fresh = tokenExpiringIn(900);
    setSession({ kind: 'guardian', accessToken: tokenExpiringIn(10), refreshToken: 'r1' });
    mockPost.mockResolvedValueOnce(reply(200, { access_token: fresh, refresh_token: 'r2' }));

    const tokens = await Promise.all([getAccessToken(), getAccessToken()]);

    expect(tokens).toEqual([fresh, fresh]);
    expect(mockPost).toHaveBeenCalledTimes(1);
    expect(mockPost).toHaveBeenCalledWith('/v1/auth/refresh', { body: { refresh_token: 'r1' } });
    expect(currentSession()).toEqual({ kind: 'guardian', accessToken: fresh, refreshToken: 'r2' });
  });

  it('reddedilen yenileme token’ı oturumu kapatır', async () => {
    setSession({ kind: 'guardian', accessToken: tokenExpiringIn(10), refreshToken: 'eski' });
    mockPost.mockResolvedValueOnce(reply(401, { detail: 'Geçersiz veya süresi dolmuş yenileme belirteci' }));

    await expect(getAccessToken()).resolves.toBeNull();
    expect(currentSession()).toBeNull();
  });

  it('sunucuya ulaşılamazsa oturumu korur', async () => {
    setSession({ kind: 'guardian', accessToken: tokenExpiringIn(10), refreshToken: 'r1' });
    mockPost.mockRejectedValueOnce(new TypeError('Network request failed'));

    await expect(getAccessToken()).resolves.toBeNull();
    expect(currentSession()).toMatchObject({ kind: 'guardian', refreshToken: 'r1' });
  });
});

describe('pairDevice', () => {
  it('cihazı çocuk moduna geçirir ve ebeveyn oturumunu iptal eder', async () => {
    setSession({ kind: 'guardian', accessToken: tokenExpiringIn(600), refreshToken: 'r1' });
    mockPost
      .mockResolvedValueOnce(reply(200, { access_token: 'cocuk-token', token_type: 'bearer' }))
      .mockResolvedValueOnce(reply(204));

    await pairDevice('cocuk-1', '123456');

    expect(mockPost).toHaveBeenNthCalledWith(1, '/v1/auth/child-pair', {
      body: { child_id: 'cocuk-1', code: '123456' },
    });
    expect(mockPost).toHaveBeenNthCalledWith(2, '/v1/auth/logout', {
      body: { refresh_token: 'r1' },
    });
    expect(currentSession()).toEqual({ kind: 'child', accessToken: 'cocuk-token' });
  });

  it('hatalı kodda mevcut oturuma dokunmaz', async () => {
    const guardian = { kind: 'guardian' as const, accessToken: tokenExpiringIn(600), refreshToken: 'r1' };
    setSession(guardian);
    mockPost.mockResolvedValueOnce(reply(400, { detail: 'Geçersiz kod' }));

    await expect(pairDevice('cocuk-1', '000000')).rejects.toMatchObject({ message: 'Geçersiz kod' });
    expect(currentSession()).toEqual(guardian);
  });
});

describe('signOut', () => {
  it('ebeveyn çıkışında yenileme token’ını sunucuda iptal eder', async () => {
    setSession({ kind: 'guardian', accessToken: tokenExpiringIn(600), refreshToken: 'r1' });
    mockPost.mockResolvedValueOnce(reply(204));

    await signOut();

    expect(mockPost).toHaveBeenCalledWith('/v1/auth/logout', { body: { refresh_token: 'r1' } });
    expect(currentSession()).toBeNull();
  });
});
