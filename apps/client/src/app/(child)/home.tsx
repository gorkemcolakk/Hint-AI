import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { ActivityIndicator, StyleSheet, Text } from 'react-native';

import { api } from '@/api/client';
import { ApiError, describeError, unwrap } from '@/api/errors';
import { signOut } from '@/auth/auth';
import { Button } from '@/components/button';
import { ErrorMessage } from '@/components/error-message';
import { Screen } from '@/components/screen';
import { Colors } from '@/constants/theme';

export default function ChildHomeScreen() {
  const me = useQuery({
    queryKey: ['me'],
    queryFn: () => unwrap(api.GET('/v1/children/me')),
    retry: false,
  });
  const [confirmUnpair, setConfirmUnpair] = useState(false);
  // Çocuk token'ı 30 dakikada biter (M1-4); rıza geri çekilirse de 403 döner.
  const sessionEnded =
    me.error instanceof ApiError && (me.error.status === 401 || me.error.status === 403);

  if (sessionEnded) {
    return (
      <Screen
        title="Oturumun sona erdi"
        subtitle="Devam etmek için ebeveyninden yeni bir eşleştirme bağlantısı iste.">
        <Button label="Tamam" color={Colors.child} onPress={() => void signOut()} />
      </Screen>
    );
  }

  return (
    <Screen>
      {me.isPending ? <ActivityIndicator size="large" color={Colors.child} /> : null}
      {me.isError ? (
        <>
          <ErrorMessage message={describeError(me.error)} />
          <Button
            label="Tekrar dene"
            variant="secondary"
            color={Colors.child}
            onPress={() => me.refetch()}
          />
        </>
      ) : null}
      {me.data ? (
        <>
          <Text accessibilityRole="header" style={styles.greeting}>
            Merhaba, {me.data.nickname}!
          </Text>
          <Text style={styles.body}>
            Yakında burada sorularını yazıp adım adım ipucu alabileceksin. Cevabı ben söylemeyeceğim;
            birlikte bulacağız.
          </Text>
          <Text style={styles.disclaimer}>
            Ben bir yapay zekâ öğrenme arkadaşıyım ve bazen yanılabilirim.
          </Text>
        </>
      ) : null}
      {confirmUnpair ? (
        <>
          <Text style={styles.body}>
            Eşleşme kaldırılırsa tekrar bağlanmak için ebeveyninden yeni bağlantı gerekir.
          </Text>
          <Button label="Eşleşmeyi kaldır" color={Colors.child} onPress={() => void signOut()} />
          <Button
            label="Vazgeç"
            variant="secondary"
            color={Colors.child}
            onPress={() => setConfirmUnpair(false)}
          />
        </>
      ) : (
        <Button
          label="Bu cihazın eşleşmesini kaldır"
          variant="secondary"
          color={Colors.child}
          onPress={() => setConfirmUnpair(true)}
        />
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  greeting: {
    fontSize: 32,
    fontWeight: '800',
    color: Colors.child,
  },
  body: {
    fontSize: 18,
    lineHeight: 26,
    color: Colors.text,
  },
  disclaimer: {
    fontSize: 14,
    color: Colors.textMuted,
  },
});
