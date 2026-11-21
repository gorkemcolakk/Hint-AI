/** JWT gövdesini okur. İmza doğrulanmaz; yalnızca istemci kararları (yenileme, yönlendirme) için. */
function readClaims(token: string): Record<string, unknown> | null {
  const payload = token.split('.')[1];
  if (!payload) {
    return null;
  }
  try {
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=');
    const claims: unknown = JSON.parse(atob(padded));
    return typeof claims === 'object' && claims !== null
      ? (claims as Record<string, unknown>)
      : null;
  } catch {
    return null;
  }
}

/** JWT'nin bitiş zamanını (ms) okur; token'ın ne zaman yenileneceğine karar vermek için. */
export function tokenExpiresAt(token: string): number | null {
  const exp = readClaims(token)?.exp;
  return typeof exp === 'number' ? exp * 1000 : null;
}

/** Token'daki rol (guardian, teacher, child). Yetki sunucuda kontrol edilir; bu yalnızca yönlendirme içindir. */
export function tokenRole(token: string): string | null {
  const role = readClaims(token)?.role;
  return typeof role === 'string' ? role : null;
}
