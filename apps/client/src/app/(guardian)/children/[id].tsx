import { useMutation, useQuery } from '@tanstack/react-query';
import * as Linking from 'expo-linking';
import { useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, Platform, Share, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import { describeError, unwrap } from '@/api/errors';
import { pairDevice } from '@/auth/auth';
import { Button } from '@/components/button';
import { ErrorMessage } from '@/components/error-message';
import { Screen } from '@/components/screen';
import { Colors, Radius, Spacing } from '@/constants/theme';

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
}

export default function ChildDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [confirmSwitch, setConfirmSwitch] = useState(false);

  const profile = useQuery({
    queryKey: ['children', id],
    queryFn: () =>
      unwrap(api.GET('/v1/children/{child_id}', { params: { path: { child_id: id } } })),
  });
  const pairing = useMutation({
    mutationFn: () =>
      unwrap(
        api.POST('/v1/children/{child_id}/device-pairing', {
          params: { path: { child_id: id } },
        }),
      ),
    onSuccess: () => setConfirmSwitch(false),
  });
  // Oturum çocuğa geçince ebeveyn ekranlarının koruması kalkar; kök düzen çocuk moduna yönlendirir.
  const switchDevice = useMutation({ mutationFn: (code: string) => pairDevice(id, code) });

  const pairingCode = pairing.data?.code ?? null;
  const pairingLink = pairingCode
    ? Linking.createURL('/pair', { queryParams: { child: id, code: pairingCode } })
    : null;
  const actionError = pairing.error ?? switchDevice.error;

  return (
    <Screen hasHeader>
      {profile.isPending ? <ActivityIndicator color={Colors.guardian} /> : null}
      {profile.isError ? <ErrorMessage message={describeError(profile.error)} /> : null}
      {profile.data ? (
        <View style={styles.card}>
          <Text accessibilityRole="header" style={styles.name}>
            {profile.data.nickname}
          </Text>
          <Text style={styles.meta}>
            {profile.data.grade}. sınıf · {profile.data.age_band} yaş · doğum yılı{' '}
            {profile.data.birth_year}
          </Text>
        </View>
      ) : null}

      <Text accessibilityRole="header" style={styles.section}>
        Cihaz eşleştirme
      </Text>
      <Text style={styles.note}>
        Çocuğunun cihazını bağlamak için tek kullanımlık bir bağlantı oluştur. Bağlantı 10 dakika
        geçerlidir; çocuğun e-posta ya da şifre girmez.
      </Text>

      {pairingCode && pairingLink && pairing.data ? (
        <View style={styles.card}>
          <Text style={styles.label}>Eşleştirme bağlantısı</Text>
          <Text selectable style={styles.link}>
            {pairingLink}
          </Text>
          <Text style={styles.meta}>
            Kod: {pairingCode} · Son geçerlilik: {formatTime(pairing.data.expires_at)}
          </Text>
          {Platform.OS !== 'web' ? (
            <Button
              label="Bağlantıyı paylaş"
              variant="secondary"
              onPress={() => void Share.share({ message: pairingLink })}
            />
          ) : null}
          {confirmSwitch ? (
            <>
              <Text style={styles.warning}>
                Bu cihaz çocuk moduna geçecek ve ebeveyn oturumun kapanacak. Emin misin?
              </Text>
              <Button
                label="Evet, çocuk moduna geç"
                color={Colors.child}
                loading={switchDevice.isPending}
                onPress={() => switchDevice.mutate(pairingCode)}
              />
              <Button label="Vazgeç" variant="secondary" onPress={() => setConfirmSwitch(false)} />
            </>
          ) : (
            <Button
              label="Bu cihazı çocuk moduna geçir"
              variant="secondary"
              color={Colors.child}
              onPress={() => setConfirmSwitch(true)}
            />
          )}
        </View>
      ) : null}

      <ErrorMessage message={actionError ? describeError(actionError) : null} />
      <Button
        label={pairingCode ? 'Yeni bağlantı oluştur' : 'Eşleştirme bağlantısı oluştur'}
        onPress={() => pairing.mutate()}
        loading={pairing.isPending}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: Spacing.md,
    gap: Spacing.sm,
  },
  name: {
    fontSize: 24,
    fontWeight: '700',
    color: Colors.text,
  },
  meta: {
    fontSize: 14,
    color: Colors.textMuted,
  },
  section: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.text,
  },
  note: {
    fontSize: 14,
    lineHeight: 20,
    color: Colors.textMuted,
  },
  label: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.text,
  },
  link: {
    fontSize: 14,
    color: Colors.guardian,
  },
  warning: {
    fontSize: 15,
    lineHeight: 21,
    color: Colors.danger,
  },
});
