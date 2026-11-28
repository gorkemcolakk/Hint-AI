import { useMutation } from '@tanstack/react-query';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { describeError } from '@/api/errors';
import { pairDevice } from '@/auth/auth';
import { useSession } from '@/auth/session-store';
import { Button } from '@/components/button';
import { ErrorMessage } from '@/components/error-message';
import { Screen } from '@/components/screen';
import { TextField } from '@/components/text-field';
import { Colors, Radius, Spacing } from '@/constants/theme';
import { parsePairingInput } from '@/features/children/pairing-input';

export default function PairScreen() {
  const { child, code } = useLocalSearchParams<{ child?: string; code?: string }>();
  const session = useSession();
  const [manualInput, setManualInput] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const pairing = useMutation({
    mutationFn: (params: { childId: string; code: string }) =>
      pairDevice(params.childId, params.code),
    onSuccess: () => router.replace('/home'),
  });

  const urlChildId = typeof child === 'string' && child.length > 0 ? child : null;
  const urlCode = typeof code === 'string' && /^\d{6}$/.test(code) ? code : null;
  const hasValidUrlParams = Boolean(urlChildId && urlCode);

  function submitManual() {
    const parsed = parsePairingInput(manualInput);
    if (!parsed.ok) {
      setFormError(parsed.error);
      return;
    }
    setFormError(null);
    pairing.mutate({ childId: parsed.childId, code: parsed.code });
  }

  return (
    <Screen title="Cihaz eşleştirme" subtitle="Bu cihaz Hint.ai çocuk modunda kullanılacak.">
      {session?.kind === 'guardian' || session?.kind === 'teacher' ? (
        <Text style={styles.warning}>Bu cihazdaki yetişkin oturumu kapatılacak.</Text>
      ) : null}
      {session?.kind === 'child' ? (
        <Text style={styles.body}>
          Bu cihaz zaten eşleşmiş; yeni bağlantıyla yeniden eşleşebilir.
        </Text>
      ) : null}

      {hasValidUrlParams && urlChildId && urlCode ? (
        <>
          <View style={styles.readyCard}>
            <Text style={styles.readyLabel}>Eşleştirme kodu hazır</Text>
            <Text style={styles.readyCode}>{urlCode}</Text>
            <Text style={styles.note}>
              Onayladığında bu cihazda çocuk ekranı açılır; şifre ya da e-posta gerekmez.
            </Text>
          </View>
          <ErrorMessage message={pairing.error ? describeError(pairing.error) : null} />
          <Button
            label="Eşleştir ve başla"
            color={Colors.child}
            loading={pairing.isPending}
            onPress={() => pairing.mutate({ childId: urlChildId, code: urlCode })}
          />
        </>
      ) : (
        <View style={styles.manualCard}>
          {child || code ? (
            <Text style={styles.warning}>
              Açtığın bağlantı eksik ya da süresi dolmuş görünüyor. Aşağıya yeni bağlantıyı
              yapıştırabilirsin.
            </Text>
          ) : (
            <Text style={styles.body}>
              Ebeveyn panelinde çocuk profilinden oluşturulan tek kullanımlık eşleştirme
              bağlantısını buraya yapıştır:
            </Text>
          )}
          <TextField
            label="Eşleştirme bağlantısı"
            hint="Örnek: http://.../pair?child=...&code=123456"
            value={manualInput}
            onChangeText={setManualInput}
            autoCapitalize="none"
            autoCorrect={false}
            editable={!pairing.isPending}
          />
          <ErrorMessage
            message={formError ?? (pairing.error ? describeError(pairing.error) : null)}
          />
          <Button
            label="Cihazı eşleştir"
            color={Colors.child}
            loading={pairing.isPending}
            disabled={manualInput.trim().length === 0}
            onPress={submitManual}
          />
        </View>
      )}

      <Button
        label="Geri dön"
        variant="secondary"
        color={Colors.textMuted}
        disabled={pairing.isPending}
        onPress={() => router.replace('/')}
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
  readyCard: {
    gap: Spacing.xs,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 2,
    borderColor: Colors.child,
    backgroundColor: '#E6F4F1',
  },
  readyLabel: {
    fontSize: 13,
    fontWeight: '700',
    textTransform: 'uppercase',
    color: Colors.child,
  },
  readyCode: {
    fontSize: 32,
    fontWeight: '800',
    letterSpacing: 4,
    color: Colors.text,
    fontVariant: ['tabular-nums'],
  },
  manualCard: {
    gap: Spacing.md,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
  },
  note: {
    fontSize: 14,
    lineHeight: 20,
    color: Colors.text,
  },
});
