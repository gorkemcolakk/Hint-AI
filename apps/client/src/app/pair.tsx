import { useMutation } from '@tanstack/react-query';
import { router, useLocalSearchParams } from 'expo-router';
import { StyleSheet, Text } from 'react-native';

import { describeError } from '@/api/errors';
import { pairDevice } from '@/auth/auth';
import { useSession } from '@/auth/session-store';
import { Button } from '@/components/button';
import { ErrorMessage } from '@/components/error-message';
import { Screen } from '@/components/screen';
import { Colors } from '@/constants/theme';

export default function PairScreen() {
  const { child, code } = useLocalSearchParams<{ child?: string; code?: string }>();
  const session = useSession();
  const pairing = useMutation({
    mutationFn: (params: { childId: string; code: string }) =>
      pairDevice(params.childId, params.code),
    onSuccess: () => router.replace('/home'),
  });

  const childId = typeof child === 'string' && child.length > 0 ? child : null;
  const pairingCode = typeof code === 'string' && /^\d{6}$/.test(code) ? code : null;

  if (!childId || !pairingCode) {
    return (
      <Screen title="Cihaz eşleştirme">
        <Text style={styles.body}>
          Bu bağlantı eksik ya da hatalı. Ebeveyninden yeni bir eşleştirme bağlantısı iste.
        </Text>
      </Screen>
    );
  }

  return (
    <Screen title="Cihaz eşleştirme" subtitle="Bu cihaz Hint.ai çocuk modunda kullanılacak.">
      {session?.kind === 'guardian' ? (
        <Text style={styles.warning}>Bu cihazdaki ebeveyn oturumu kapatılacak.</Text>
      ) : null}
      {session?.kind === 'child' ? (
        <Text style={styles.body}>Bu cihaz zaten eşleşmiş; yeni bağlantıyla yeniden eşleşebilir.</Text>
      ) : null}
      <ErrorMessage message={pairing.error ? describeError(pairing.error) : null} />
      <Button
        label="Eşleştir"
        color={Colors.child}
        loading={pairing.isPending}
        onPress={() => pairing.mutate({ childId, code: pairingCode })}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  body: {
    fontSize: 16,
    lineHeight: 22,
    color: Colors.text,
  },
  warning: {
    fontSize: 15,
    lineHeight: 21,
    color: Colors.danger,
  },
});
