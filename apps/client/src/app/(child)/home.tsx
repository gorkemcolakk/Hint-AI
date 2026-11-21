import { useMutation } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import { ApiError, describeError, unwrap } from '@/api/errors';
import { signOut } from '@/auth/auth';
import { Button } from '@/components/button';
import { ErrorMessage } from '@/components/error-message';
import { Screen } from '@/components/screen';
import { TextField } from '@/components/text-field';
import { Colors, Radius, Spacing } from '@/constants/theme';
import { type SafetyNotice, SupportCard } from '@/features/safety/support-card';
import { themeForAgeBand } from '@/features/tutoring/ladder';
import { useChildProfile } from '@/features/tutoring/use-child-theme';

export default function ChildHomeScreen() {
  const me = useChildProfile();
  const theme = themeForAgeBand(me.data?.age_band);
  const [question, setQuestion] = useState('');
  const [confirmUnpair, setConfirmUnpair] = useState(false);
  const [safety, setSafety] = useState<SafetyNotice | null>(null);

  const submit = useMutation({
    mutationFn: (text: string) => unwrap(api.POST('/v1/problems', { body: { text } })),
    onSuccess: (problem) => {
      setQuestion('');
      // Güvenlik kapısı akışı durdurduysa soru oluşturulmaz; destek kartı gösterilir.
      if (problem.safety || !problem.id) {
        setSafety(problem.safety ?? null);
        return;
      }
      setSafety(null);
      router.push({
        pathname: '/problem/[id]',
        params: problem.notice ? { id: problem.id, notice: problem.notice } : { id: problem.id },
      });
    },
  });

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
      {me.isPending ? <ActivityIndicator size="large" color={theme.accent} /> : null}
      {me.isError ? (
        <>
          <ErrorMessage message={describeError(me.error)} />
          <Button
            label="Tekrar dene"
            variant="secondary"
            color={theme.accent}
            onPress={() => me.refetch()}
          />
        </>
      ) : null}
      {me.data ? (
        <>
          <Text accessibilityRole="header" style={[styles.greeting, { color: theme.accent }]}>
            Merhaba, {me.data.nickname}!{theme.emoji ? ' 👋' : ''}
          </Text>
          <Text style={[styles.body, { fontSize: 18 * theme.fontScale }]}>
            Takıldığın matematik sorusunu yaz. Cevabı ben söylemeyeceğim; adım adım ipucu vereceğim,
            sen bulacaksın.
          </Text>

          {safety ? <SupportCard notice={safety} /> : null}

          <View style={[styles.card, { borderColor: theme.accent }]}>
            <TextField
              label="Sorun ne?"
              hint="Örnek: 3x + 5 = 20 ise x kaçtır?"
              value={question}
              onChangeText={setQuestion}
              multiline
              maxLength={2000}
              style={styles.questionInput}
              editable={!submit.isPending}
            />
            <ErrorMessage message={submit.isError ? describeError(submit.error) : null} />
            <Button
              label={submit.isPending ? 'Soruna bakıyorum…' : 'Soruyu gönder'}
              color={theme.accent}
              loading={submit.isPending}
              disabled={question.trim().length === 0}
              onPress={() => submit.mutate(question.trim())}
            />
          </View>

          <Text style={styles.disclaimer}>
            Ben bir yapay zekâ öğrenme arkadaşıyım ve bazen yanılabilirim. Adını, okulunu ya da
            telefonunu yazmana gerek yok.
          </Text>
        </>
      ) : null}
      {confirmUnpair ? (
        <>
          <Text style={styles.body}>
            Eşleşme kaldırılırsa tekrar bağlanmak için ebeveyninden yeni bağlantı gerekir.
          </Text>
          <Button label="Eşleşmeyi kaldır" color={theme.accent} onPress={() => void signOut()} />
          <Button
            label="Vazgeç"
            variant="secondary"
            color={theme.accent}
            onPress={() => setConfirmUnpair(false)}
          />
        </>
      ) : (
        <Button
          label="Bu cihazın eşleşmesini kaldır"
          variant="secondary"
          color={theme.accent}
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
  },
  body: {
    lineHeight: 26,
    color: Colors.text,
  },
  card: {
    gap: Spacing.md,
    padding: Spacing.md,
    borderWidth: 2,
    borderRadius: Radius.md,
    backgroundColor: Colors.surface,
  },
  questionInput: {
    minHeight: 96,
    paddingTop: Spacing.sm,
    textAlignVertical: 'top',
  },
  disclaimer: {
    fontSize: 14,
    color: Colors.textMuted,
  },
});
