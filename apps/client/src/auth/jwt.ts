/**
 * JWT'nin bitiş zamanını (ms) okur. İmza doğrulanmaz; yalnızca token'ın ne zaman
 * yenileneceğine karar vermek için kullanılır.
 */
export function tokenExpiresAt(token: string): number | null {
  const payload = token.split('.')[1];
  if (!payload) {
    return null;
  }
  try {
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=');
    const claims: unknown = JSON.parse(atob(padded));
    if (typeof claims === 'object' && claims !== null && 'exp' in claims) {
      return typeof claims.exp === 'number' ? claims.exp * 1000 : null;
    }
    return null;
  } catch {
    return null;
  }
}
