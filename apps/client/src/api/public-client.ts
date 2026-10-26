import createClient from 'openapi-fetch';

import { API_BASE_URL } from '@/config';

import type { paths } from './schema';

/** Kimlik gerektirmeyen uçlar (giriş, kayıt, yenileme, eşleştirme) için istemci. */
export const publicApi = createClient<paths>({ baseUrl: API_BASE_URL });
