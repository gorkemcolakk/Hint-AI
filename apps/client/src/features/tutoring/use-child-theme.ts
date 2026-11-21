import { useQuery } from '@tanstack/react-query';

import { api } from '@/api/client';
import { unwrap } from '@/api/errors';
import { type ChildTheme, themeForAgeBand } from '@/features/tutoring/ladder';

/** Çocuk profilini (önbellekten) okur ve yaş bandına uygun temayı döner. */
export function useChildProfile() {
  return useQuery({
    queryKey: ['me'],
    queryFn: () => unwrap(api.GET('/v1/children/me')),
    retry: false,
  });
}

export function useChildTheme(): ChildTheme {
  const me = useChildProfile();
  return themeForAgeBand(me.data?.age_band);
}
