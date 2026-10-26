import { Redirect } from 'expo-router';

import { useSession } from '@/auth/session-store';

export default function Index() {
  const session = useSession();
  if (session?.kind === 'guardian') {
    return <Redirect href="/children" />;
  }
  if (session?.kind === 'child') {
    return <Redirect href="/home" />;
  }
  return <Redirect href="/welcome" />;
}
