import { useMutation } from '@tanstack/react-query';
import { router } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { describeError } from '@/api/errors';
import { devSignInAsChild, devSignInAsGuardian, devSignInAsTeacher } from '@/auth/auth';
import { Button } from '@/components/button';
import { ErrorMessage } from '@/components/error-message';
import { Screen } from '@/components/screen';
import { Colors, Radius, Spacing } from '@/constants/theme';

export default function WelcomeScreen() {
  return (
    <Screen>
      <View style={styles.hero}>
        <Text accessibilityRole="header" style={styles.brand}>
          Hint.ai
        </Text>
        <Text style={styles.tagline}>Cevabı değil, ipucunu veren öğrenme arkadaşı.</Text>
      </View>
      {__DEV__ ? <DevShortcuts /> : null}
      <Button label="Giriş yap" onPress={() => router.push('/login')} />
      <Button
        label="Ebeveyn hesabı oluştur"
        variant="secondary"
        onPress={() => router.push('/register')}
      />
      <Button
        label="Öğretmen hesabı oluştur"
        variant="secondary"
        color={Colors.teacher}
        onPress={() => router.push({ pathname: '/register', params: { role: 'teacher' } })}
      />
      <Text style={styles.note}>
        Çocuğunun cihazını mı bağlıyorsun? Ebeveyn panelinde oluşturduğun eşleştirme bağlantısını bu
        cihazda aç.
      </Text>
    </Screen>
  );
}

/** Yalnızca geliştirme derlemesinde görünür; sunucuda HINT_DEV_SHORTCUTS=true gerekir. */
function DevShortcuts() {
  const child = useMutation({ mutationFn: devSignInAsChild });
  const guardian = useMutation({ mutationFn: devSignInAsGuardian });
  const teacher = useMutation({ mutationFn: devSignInAsTeacher });
  const error = child.error ?? guardian.error ?? teacher.error;
  const busy = child.isPending || guardian.isPending || teacher.isPending;

  return (
    <View style={styles.devBox}>
      <Text style={styles.devTitle}>Yerel deneme</Text>
      <Button
        label="Demo çocuk olarak gir"
        color={Colors.child}
        loading={child.isPending}
        disabled={busy}
        onPress={() => child.mutate()}
      />
      <Button
        label="Demo ebeveyn olarak gir"
        variant="secondary"
        loading={guardian.isPending}
        disabled={busy}
        onPress={() => guardian.mutate()}
      />
      <Button
        label="Demo öğretmen olarak gir"
        variant="secondary"
        color={Colors.teacher}
        loading={teacher.isPending}
        disabled={busy}
        onPress={() => teacher.mutate()}
      />
      <ErrorMessage message={error ? describeError(error) : null} />
      <Text style={styles.note}>
        Sahte veriyle çalışır. Web’de sayfa yenilenince oturum kapanır; buradan tekrar girebilirsin.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  hero: {
    alignItems: 'center',
    gap: Spacing.sm,
    paddingVertical: Spacing.xl,
  },
  brand: {
    fontSize: 40,
    fontWeight: '800',
    color: Colors.guardian,
  },
  tagline: {
    fontSize: 17,
    textAlign: 'center',
    color: Colors.textMuted,
  },
  note: {
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
    color: Colors.textMuted,
  },
  devBox: {
    gap: Spacing.sm,
    padding: Spacing.md,
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: Colors.border,
    borderRadius: Radius.md,
    backgroundColor: Colors.surface,
  },
  devTitle: {
    fontSize: 13,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    color: Colors.textMuted,
  },
});
