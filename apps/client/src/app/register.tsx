import { useMutation } from '@tanstack/react-query';
import { Link } from 'expo-router';
import { useState } from 'react';
import { StyleSheet } from 'react-native';

import { describeError } from '@/api/errors';
import { register } from '@/auth/auth';
import { Button } from '@/components/button';
import { ErrorMessage } from '@/components/error-message';
import { Screen } from '@/components/screen';
import { TextField } from '@/components/text-field';
import { Colors } from '@/constants/theme';

const MIN_PASSWORD_LENGTH = 8;

export default function RegisterScreen() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const signUp = useMutation({
    mutationFn: () =>
      register({ email: email.trim(), password, fullName: fullName.trim() || undefined }),
  });

  function submit() {
    if (!email.trim()) {
      setFormError('E-posta gerekli.');
      return;
    }
    if (password.length < MIN_PASSWORD_LENGTH) {
      setFormError(`Parola en az ${MIN_PASSWORD_LENGTH} karakter olmalı.`);
      return;
    }
    setFormError(null);
    signUp.mutate();
  }

  return (
    <Screen
      hasHeader
      title="Ebeveyn hesabı"
      subtitle="Çocuğunun profilini ve rıza tercihlerini bu hesaptan yöneteceksin.">
      <TextField
        label="Ad soyad (isteğe bağlı)"
        value={fullName}
        onChangeText={setFullName}
        autoComplete="name"
      />
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
        hint={`En az ${MIN_PASSWORD_LENGTH} karakter`}
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        autoComplete="new-password"
      />
      <ErrorMessage message={formError ?? (signUp.error ? describeError(signUp.error) : null)} />
      <Button label="Hesap oluştur" onPress={submit} loading={signUp.isPending} />
      <Link href="/login" style={styles.link}>
        Zaten hesabın var mı? Giriş yap
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
