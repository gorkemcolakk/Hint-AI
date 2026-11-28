import { useMutation } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import { ApiError, describeError, unwrap } from '@/api/errors';
import { signOut } from '@/auth/auth';
import { Button } from '@/components/button';
import { ErrorMessage } from '@/components/error-message';
import { MathText } from '@/components/math-text';
import { Screen } from '@/components/screen';
import { TextField } from '@/components/text-field';
import { Colors, Radius, Spacing } from '@/constants/theme';
import { type SafetyNotice, SupportCard } from '@/features/safety/support-card';
import { themeForAgeBand } from '@/features/tutoring/ladder';
import { isQuotaError, QuotaChecklistCard } from '@/features/tutoring/quota-checklist';
import {
  dismissBreakReminder,
  rememberRecentProblem,
  setComfortableReading,
  shouldSuggestBreak,
  useChildUiState,
} from '@/features/tutoring/reading-preferences';
import { useChildProfile } from '@/features/tutoring/use-child-theme';

const SAMPLE_QUESTIONS = [
  { label: 'Denklem', text: '3x + 5 = 20 ise x kaçtır?' },
  { label: 'Kesir', text: 'Bir pastanın 2/5’ini Ali, 1/5’ini Ece yedi. Geriye kaçta kaçı kaldı?' },
  { label: 'Yüzde', text: '240 TL olan bir kitabın %25 indirimli fiyatı kaç TL olur?' },
  { label: 'Üçgen', text: 'İki iç açısı 55° ve 65° olan üçgenin üçüncü iç açısı kaç derecedir?' },
] as const;

export default function ChildHomeScreen() {
  const me = useChildProfile();
  const ui = useChildUiState();
  const theme = themeForAgeBand(me.data?.age_band);
  const [question, setQuestion] = useState('');
  const [confirmUnpair, setConfirmUnpair] = useState(false);
  const [showPhotoInfo, setShowPhotoInfo] = useState(false);
  const [safety, setSafety] = useState<SafetyNotice | null>(null);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 60_000);
    return () => clearInterval(timer);
  }, []);

  const submit = useMutation({
    mutationFn: (text: string) => unwrap(api.POST('/v1/problems', { body: { text } })),
    onSuccess: (problem, submittedText) => {
      setQuestion('');
      // Güvenlik kapısı akışı durdurduysa soru oluşturulmaz; destek kartı gösterilir.
      if (problem.safety || !problem.id) {
        setSafety(problem.safety ?? null);
        return;
      }
      setSafety(null);
      rememberRecentProblem({
        id: problem.id,
        preview: submittedText,
        topic: problem.topic ?? null,
        solved: false,
      });
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

  const quotaHit = submit.isError && isQuotaError(submit.error);
  const showBreak = shouldSuggestBreak(now, ui);

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
          <View style={styles.topBar}>
            <View style={[styles.modeBadge, { backgroundColor: theme.accentSoft }]}>
              <Text style={[styles.modeBadgeText, { color: theme.accent }]}>
                {theme.name === 'odak' ? 'Odak Modu · 14–17' : 'Keşif Modu · 7–13'}
              </Text>
            </View>
            <Pressable
              accessibilityRole="switch"
              accessibilityLabel="Rahat okuma modu"
              accessibilityState={{ checked: ui.comfortableReading }}
              aria-checked={ui.comfortableReading}
              onPress={() => setComfortableReading(!ui.comfortableReading)}
              style={[
                styles.readingToggle,
                ui.comfortableReading && {
                  backgroundColor: theme.accentSoft,
                  borderColor: theme.accent,
                },
              ]}>
              <Text
                style={[
                  styles.readingToggleText,
                  ui.comfortableReading && { color: theme.accent, fontWeight: '700' },
                ]}>
                Aa Rahat okuma {ui.comfortableReading ? 'açık' : 'kapalı'}
              </Text>
            </Pressable>
          </View>

          <Text accessibilityRole="header" style={[styles.greeting, { color: theme.accent }]}>
            Merhaba, {me.data.nickname}!{theme.emoji ? ' 👋' : ''}
          </Text>
          <MathText
            comfortableReading={ui.comfortableReading}
            style={[styles.body, { fontSize: 18 * theme.fontScale }]}>
            Takıldığın matematik sorusunu yaz. Cevabı ben söylemeyeceğim; adım adım ipucu vereceğim,
            sen bulacaksın.
          </MathText>

          {showBreak ? (
            <View role="status" style={[styles.breakBanner, { borderColor: theme.accent }]}>
              <Text style={styles.breakText}>
                {theme.emoji ? '💧 ' : ''}30 dakikadır harika odaklandın! Gözlerini dinlendirmek
                için kısa bir su molası vermek ister misin?
              </Text>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Mola hatırlatmasını kapat"
                onPress={dismissBreakReminder}
                style={styles.breakDismiss}>
                <Text style={[styles.breakDismissText, { color: theme.accent }]}>Tamam</Text>
              </Pressable>
            </View>
          ) : null}

          {ui.recentProblem && !ui.recentProblem.solved ? (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`Son soruna dön: ${ui.recentProblem.preview}`}
              onPress={() =>
                router.push({ pathname: '/problem/[id]', params: { id: ui.recentProblem!.id } })
              }
              style={({ pressed }) => [
                styles.recentCard,
                { borderColor: theme.accent, backgroundColor: theme.accentSoft },
                pressed && styles.pressed,
              ]}>
              <Text style={[styles.recentLabel, { color: theme.accent }]}>
                {ui.recentProblem.topic
                  ? `Kaldığın yerden devam et · ${ui.recentProblem.topic}`
                  : 'Kaldığın yerden devam et'}
              </Text>
              <Text style={styles.recentPreview} numberOfLines={2}>
                {ui.recentProblem.preview}
              </Text>
            </Pressable>
          ) : null}

          {safety ? <SupportCard notice={safety} /> : null}
          {quotaHit ? <QuotaChecklistCard theme={theme} /> : null}

          <View style={[styles.card, { borderColor: theme.accent }]}>
            <TextField
              label="Sorun ne?"
              hint="Örnek: 3x + 5 = 20 ise x kaçtır?"
              value={question}
              onChangeText={setQuestion}
              multiline
              maxLength={2000}
              style={[styles.questionInput, ui.comfortableReading && styles.comfortableInput]}
              editable={!submit.isPending}
            />

            <View style={styles.samplesBlock}>
              <Text style={styles.samplesLabel}>Hızlı denemek için örnek seçebilirsin:</Text>
              <View style={styles.samplesRow}>
                {SAMPLE_QUESTIONS.map((sample) => (
                  <Pressable
                    key={sample.label}
                    accessibilityRole="button"
                    accessibilityLabel={`${sample.label} örneğini doldur`}
                    disabled={submit.isPending}
                    onPress={() => setQuestion(sample.text)}
                    style={({ pressed }) => [
                      styles.sampleChip,
                      { borderColor: theme.accent },
                      pressed && styles.pressed,
                    ]}>
                    <Text style={[styles.sampleChipText, { color: theme.accent }]}>
                      {sample.label}
                    </Text>
                  </Pressable>
                ))}
              </View>
            </View>

            {!quotaHit ? (
              <ErrorMessage message={submit.isError ? describeError(submit.error) : null} />
            ) : null}

            <Button
              label={submit.isPending ? 'Soruna bakıyorum…' : 'Soruyu gönder'}
              color={theme.accent}
              loading={submit.isPending}
              disabled={question.trim().length === 0}
              onPress={() => submit.mutate(question.trim())}
            />

            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Fotoğraftan soru ekleme bilgisi"
              onPress={() => setShowPhotoInfo((prev) => !prev)}
              style={styles.photoLink}>
              <Text style={styles.photoLinkText}>📷 Fotoğraftan soru yükleme (Faz 2’de)</Text>
            </Pressable>
            {showPhotoInfo ? (
              <Text style={styles.photoNote}>
                Soru fotoğrafından metin okuma (OCR) özelliği bir sonraki aşamada eklenecek. Şimdilik
                sorudaki sayıları ve isteneni yukarıdaki kutuya yazabilirsin.
              </Text>
            ) : null}
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
  topBar: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: Spacing.sm,
  },
  modeBadge: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: 6,
    borderRadius: Radius.md,
  },
  modeBadgeText: {
    fontSize: 13,
    fontWeight: '700',
  },
  readingToggle: {
    minHeight: 36,
    paddingHorizontal: Spacing.sm,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
    justifyContent: 'center',
  },
  readingToggleText: {
    fontSize: 13,
    color: Colors.textMuted,
  },
  greeting: {
    fontSize: 32,
    fontWeight: '800',
  },
  body: {
    lineHeight: 26,
    color: Colors.text,
  },
  breakBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1,
    backgroundColor: Colors.surface,
  },
  breakText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
    color: Colors.text,
  },
  breakDismiss: {
    minHeight: 36,
    paddingHorizontal: Spacing.sm,
    justifyContent: 'center',
  },
  breakDismissText: {
    fontSize: 14,
    fontWeight: '700',
  },
  recentCard: {
    gap: 4,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1.5,
  },
  recentLabel: {
    fontSize: 13,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  recentPreview: {
    fontSize: 15,
    fontWeight: '600',
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
  comfortableInput: {
    letterSpacing: 0.6,
    lineHeight: 26,
    fontSize: 18,
  },
  samplesBlock: {
    gap: Spacing.xs,
  },
  samplesLabel: {
    fontSize: 13,
    color: Colors.textMuted,
  },
  samplesRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.xs,
  },
  sampleChip: {
    minHeight: 36,
    paddingHorizontal: Spacing.sm,
    borderRadius: Radius.md,
    borderWidth: 1,
    backgroundColor: Colors.background,
    justifyContent: 'center',
  },
  sampleChipText: {
    fontSize: 13,
    fontWeight: '600',
  },
  photoLink: {
    alignSelf: 'center',
    paddingVertical: Spacing.xs,
  },
  photoLinkText: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textMuted,
  },
  photoNote: {
    fontSize: 13,
    lineHeight: 19,
    color: Colors.textMuted,
    textAlign: 'center',
  },
  disclaimer: {
    fontSize: 14,
    color: Colors.textMuted,
  },
  pressed: {
    opacity: 0.8,
  },
});
