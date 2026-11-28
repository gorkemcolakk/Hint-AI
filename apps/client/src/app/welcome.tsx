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
        <Text style={styles.trustBadges}>
          7–17 yaş · Sokratik ipucu merdiveni · Reklamsız ve KVKK uyumlu
        </Text>
      </View>

      {__DEV__ ? <DevShortcuts /> : null}

      <View style={styles.roleCard}>
        <Text accessibilityRole="header" style={styles.roleTitle}>
          Ebeveyn ve Öğretmen Girişi
        </Text>
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
      </View>

      <View style={styles.childBox}>
        <Text accessibilityRole="header" style={styles.childTitle}>
          Çocuk Cihazı Bağlantısı
        </Text>
        <Text style={styles.childBody}>
          Çocuğun e-posta ya da şifre kullanmaz. Ebeveyn panelinden oluşturduğun tek kullanımlık
          bağlantıyı açabilir ya da aşağıdan yapıştırabilirsin.
        </Text>
        <Button
          label="Eşleştirme bağlantısıyla katıl"
          variant="secondary"
          color={Colors.child}
          onPress={() => router.push('/pair')}
        />
      </View>
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
    gap: Spacing.xs,
    paddingVertical: Spacing.lg,
  },
  brand: {
    fontSize: 40,
    fontWeight: '800',
    color: Colors.guardian,
  },
  tagline: {
    fontSize: 17,
    textAlign: 'center',
    color: Colors.text,
    fontWeight: '600',
  },
  trustBadges: {
    fontSize: 13,
    textAlign: 'center',
    color: Colors.textMuted,
  },
  roleCard: {
    gap: Spacing.sm,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
  },
  roleTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.text,
  },
  childBox: {
    gap: Spacing.sm,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1.5,
    borderColor: Colors.child,
    backgroundColor: '#E6F4F1',
  },
  childTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.child,
  },
  childBody: {
    fontSize: 14,
    lineHeight: 20,
    color: Colors.text,
  },
  note: {
    fontSize: 13,
    lineHeight: 19,
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
