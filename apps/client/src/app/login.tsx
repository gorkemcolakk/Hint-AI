import { useMutation } from '@tanstack/react-query';
import { Link } from 'expo-router';
import { useState } from 'react';
import { StyleSheet } from 'react-native';

import { describeError } from '@/api/errors';
import { signIn } from '@/auth/auth';
import { Button } from '@/components/button';
import { ErrorMessage } from '@/components/error-message';
import { Screen } from '@/components/screen';
import { TextField } from '@/components/text-field';
import { Colors } from '@/constants/theme';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  // Giriş başarılı olunca oturum değişir; kök düzendeki koruma kullanıcıyı panele götürür.
  const login = useMutation({ mutationFn: () => signIn(email.trim(), password) });
  const canSubmit = email.trim().length > 0 && password.length > 0;

  return (
    <Screen hasHeader title="Tekrar hoş geldin">
      <TextField
        label="E-posta"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        autoComplete="email"
        keyboardType="email-address"
      />
      <TextField
        label="Parola"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        autoComplete="current-password"
        onSubmitEditing={() => canSubmit && login.mutate()}
      />
      <ErrorMessage message={login.error ? describeError(login.error) : null} />
      <Button
        label="Giriş yap"
        onPress={() => login.mutate()}
        loading={login.isPending}
        disabled={!canSubmit}
      />
      <Link href="/register" style={styles.link}>
        Hesabın yok mu? Kayıt ol
      </Link>
    </Screen>
  );
}

const styles = StyleSheet.create({
  link: {
    fontSize: 15,
    textAlign: 'center',
    color: Colors.guardian,
    textDecorationLine: 'underline',
  },
});
