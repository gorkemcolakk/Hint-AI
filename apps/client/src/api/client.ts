import createClient, { type Middleware } from 'openapi-fetch';

import { getAccessToken } from '@/auth/auth';
import { API_BASE_URL } from '@/config';

import type { paths } from './schema';

const authMiddleware: Middleware = {
  async onRequest({ request }) {
    const token = await getAccessToken();
    if (token) {
      request.headers.set('Authorization', `Bearer ${token}`);
    }
    return request;
  },
};

/** Oturum gerektiren uçlar için istemci; her isteğe güncel token eklenir. */
export const api = createClient<paths>({ baseUrl: API_BASE_URL });
api.use(authMiddleware);
