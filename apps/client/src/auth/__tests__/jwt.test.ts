import { tokenExpiresAt } from '@/auth/jwt';

function tokenWithClaims(claims: object): string {
  const payload = btoa(JSON.stringify(claims))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
  return `header.${payload}.signature`;
}

describe('tokenExpiresAt', () => {
  it('exp alanını milisaniyeye çevirir', () => {
    expect(tokenExpiresAt(tokenWithClaims({ sub: 'u1', exp: 1_800_000_000 }))).toBe(
      1_800_000_000_000,
    );
  });

  it('exp yoksa veya token bozuksa null döner', () => {
    expect(tokenExpiresAt(tokenWithClaims({ sub: 'u1' }))).toBeNull();
    expect(tokenExpiresAt('bozuk-token')).toBeNull();
    expect(tokenExpiresAt('a.%%%.c')).toBeNull();
    expect(tokenExpiresAt('')).toBeNull();
  });
});
