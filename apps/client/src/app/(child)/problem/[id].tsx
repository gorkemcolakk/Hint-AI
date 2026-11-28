import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import { describeError, unwrap } from '@/api/errors';
import { Button } from '@/components/button';
import { ErrorMessage } from '@/components/error-message';
import { MathText } from '@/components/math-text';
import { Screen } from '@/components/screen';
import { TextField } from '@/components/text-field';
import { Colors, Radius, Spacing } from '@/constants/theme';
import { NoticeText, type SafetyNotice, SupportCard } from '@/features/safety/support-card';
import { HintCard } from '@/features/tutoring/hint-card';
import { FRUSTRATION_MESSAGE, hintButtonLabel } from '@/features/tutoring/ladder';
import { LadderProgress } from '@/features/tutoring/ladder-progress';
import { isQuotaError, QuotaChecklistCard } from '@/features/tutoring/quota-checklist';
import {
  rememberRecentProblem,
  setComfortableReading,
  useChildUiState,
} from '@/features/tutoring/reading-preferences';
import { requestHintWithStream } from '@/features/tutoring/stream-hint';
import { useChildTheme } from '@/features/tutoring/use-child-theme';

type Feedback = { tone: 'success' | 'info'; text: string };

/** 90 saniye etkileşimsizlikte nazik ipucu teklifi (Bölüm 6.3). */
const INACTIVITY_PROMPT_MS = 90_000;
const CLARIFICATION_MESSAGE =
  'Son ipucunu bu sorudaki sayılarla biraz daha somut açar mısın?';

export default function ProblemScreen() {
  const { id, notice: initialNotice } = useLocalSearchParams<{ id: string; notice?: string }>();
  const theme = useChildTheme();
  const ui = useChildUiState();
  const queryClient = useQueryClient();
  const [answer, setAnswer] = useState('');
  const [hintNote, setHintNote] = useState('');
  const [showHintNote, setShowHintNote] = useState(false);
  const [streamingText, setStreamingText] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [notice, setNotice] = useState<string | null>(initialNotice ?? null);
  const [safety, setSafety] = useState<SafetyNotice | null>(null);
  const [lastInteraction, setLastInteraction] = useState(() => Date.now());
  const [idlePromptVisible, setIdlePromptVisible] = useState(false);

  const queryKey = ['problem', id];
  const problem = useQuery({
    queryKey,
    queryFn: () =>
      unwrap(
        api.GET('/v1/problems/{problem_id}', {
          params: { path: { problem_id: id } },
        }),
      ),
    enabled: Boolean(id),
  });
  const refresh = () => queryClient.invalidateQueries({ queryKey });

  function markInteraction() {
    setLastInteraction(Date.now());
    setIdlePromptVisible(false);
  }

  useEffect(() => {
    if (!problem.data) return;
    rememberRecentProblem({
      id: problem.data.id,
      preview: problem.data.text,
      topic: problem.data.topic,
      solved: problem.data.state === 'solved',
    });
  }, [problem.data]);

  const canPromptIdle =
    problem.data?.state === 'open' && Boolean(problem.data.can_request_hint) && !idlePromptVisible;

  useEffect(() => {
    if (!canPromptIdle) return;
    const timer = setTimeout(() => setIdlePromptVisible(true), INACTIVITY_PROMPT_MS);
    return () => clearTimeout(timer);
  }, [canPromptIdle, lastInteraction]);

  const hint = useMutation({
    mutationFn: (message: string | null) => {
      setStreamingText('');
      return requestHintWithStream({
        problemId: id,
        message,
        onPartialText: (partial) => setStreamingText(partial),
      });
    },
    onSuccess: (result) => {
      setStreamingText(null);
      setHintNote('');
      setShowHintNote(false);
      setFeedback(null);
      setSafety(result.safety ?? null);
      setNotice(result.notice ?? null);
      markInteraction();
      return refresh();
    },
    onError: () => {
      setStreamingText(null);
    },
  });

  const attempt = useMutation({
    mutationFn: (value: string) =>
      unwrap(
        api.POST('/v1/problems/{problem_id}/attempts', {
          params: { path: { problem_id: id } },
          body: { answer: value },
        }),
      ),
    onSuccess: (result) => {
      setNotice(null);
      setSafety(result.safety ?? null);
      setFeedback(
        result.safety ? null : { tone: result.solved ? 'success' : 'info', text: result.feedback },
      );
      if (!result.solved) setAnswer('');
      markInteraction();
      return refresh();
    },
  });

  if (problem.isPending) {
    return (
      <Screen>
        <ActivityIndicator size="large" color={theme.accent} />
      </Screen>
    );
  }
  if (problem.isError) {
    return (
      <Screen title="Soru açılamadı">
        <ErrorMessage message={describeError(problem.error)} />
        <Button label="Tekrar dene" color={theme.accent} onPress={() => problem.refetch()} />
        <Button
          label="Ana ekrana dön"
          variant="secondary"
          color={theme.accent}
          onPress={() => router.replace('/home')}
        />
      </Screen>
    );
  }

  const data = problem.data;
  const solved = data.state === 'solved';
  const busy = hint.isPending || attempt.isPending;
  const latestIndex = data.hints.length - 1;
  const actionError = hint.error ?? attempt.error;
  const quotaHit = Boolean(actionError && isQuotaError(actionError));
  const lowConfidence = data.status !== 'verified';

  return (
    <Screen>
      <View style={styles.topRow}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Ana ekrana dön"
          onPress={() => router.replace('/home')}
          style={styles.backButton}>
          <Text style={[styles.backText, { color: theme.accent }]}>← Yeni soru / Ana ekran</Text>
        </Pressable>
        <Pressable
          accessibilityRole="switch"
          accessibilityLabel="Rahat okuma modu"
          accessibilityState={{ checked: ui.comfortableReading }}
          aria-checked={ui.comfortableReading}
          onPress={() => setComfortableReading(!ui.comfortableReading)}
          style={[
            styles.readingChip,
            ui.comfortableReading && {
              backgroundColor: theme.accentSoft,
              borderColor: theme.accent,
            },
          ]}>
          <Text
            style={[
              styles.readingChipText,
              ui.comfortableReading && { color: theme.accent, fontWeight: '700' },
            ]}>
            Aa Rahat okuma
          </Text>
        </Pressable>
      </View>

      <View style={[styles.questionCard, { backgroundColor: theme.accentSoft }]}>
        <Text style={[styles.label, { color: theme.accent }]}>
          {data.topic ? `Sorun · ${data.topic}` : 'Sorun'}
        </Text>
        <MathText
          comfortableReading={ui.comfortableReading}
          style={[
            styles.question,
            { fontSize: 20 * theme.fontScale * (ui.comfortableReading ? 1.08 : 1) },
          ]}>
          {data.text}
        </MathText>
      </View>

      {lowConfidence ? (
        <View role="status" style={styles.cautionBanner}>
          <Text style={styles.cautionText}>
            Bu sorunun sayısal sonucunu otomatik olarak tam doğrulayamadım; ipuçlarıyla ilerlerken
            öğretmenine ya da ders kitabına da danışabilirsin.
          </Text>
        </View>
      ) : null}

      {notice ? <NoticeText text={notice} /> : null}
      {safety ? <SupportCard notice={safety} /> : null}

      <LadderProgress
        current={data.current_hint_level ?? null}
        maxLevel={data.max_hint_level}
        theme={theme}
      />

      {data.hints.length > 0 || streamingText !== null ? (
        <View style={styles.hints} accessibilityLiveRegion="polite">
          {data.hints.map((item, index) => (
            <HintCard
              key={item.id}
              id={item.id}
              level={item.level}
              levelName={item.level_name}
              text={item.text}
              latest={index === latestIndex && streamingText === null}
              theme={theme}
              comfortableReading={ui.comfortableReading}
              canRequestClarification={!solved && data.can_request_hint && !busy}
              onRequestClarification={() => hint.mutate(CLARIFICATION_MESSAGE)}
            />
          ))}
          {streamingText !== null ? (
            <HintCard
              level={(data.current_hint_level ?? -1) + 1}
              levelName="Yeni ipucu"
              text={streamingText || 'Sorunu düşünüyorum, ipucun hazırlanıyor…'}
              latest
              streaming
              theme={theme}
              comfortableReading={ui.comfortableReading}
            />
          ) : null}
        </View>
      ) : null}

      {idlePromptVisible && !solved && !busy && data.can_request_hint ? (
        <View role="status" style={[styles.idleCard, { borderColor: theme.accent }]}>
          <Text style={styles.idleText}>
            {theme.emoji ? '🤔 ' : ''}Bir süredir bu adım üzerinde düşünüyorsun. Küçük bir ipucu
            ister misin?
          </Text>
          <View style={styles.idleActions}>
            <Button
              label="Evet, ipucu ver"
              color={theme.accent}
              onPress={() => hint.mutate(null)}
            />
            <Button
              label="Kendim deniyorum"
              variant="secondary"
              color={Colors.textMuted}
              onPress={markInteraction}
            />
          </View>
        </View>
      ) : null}

      {feedback && !solved ? (
        <Text role="status" accessibilityLiveRegion="polite" style={styles.feedback}>
          {feedback.text}
        </Text>
      ) : null}

      {quotaHit ? (
        <QuotaChecklistCard theme={theme} />
      ) : (
        <ErrorMessage message={actionError ? describeError(actionError) : null} />
      )}

      {solved ? (
        <View style={[styles.celebrationCard, { borderColor: theme.accent }]}>
          <Text
            role="status"
            accessibilityLiveRegion="polite"
            style={[styles.celebrationTitle, { color: theme.accent }]}>
            {theme.emoji ? '🎉 ' : ''}
            {feedback?.text ?? 'Harika, doğru cevabı buldun!'}
          </Text>
          <Text style={styles.celebrationSub}>
            {data.hints.length === 0
              ? 'Hiç ipucu kullanmadan tamamen kendi başına çözdün.'
              : `${data.hints.length} ipucu basamağıyla adım adım düşünerek kendin çözdün.`}
          </Text>
          <Button
            label="Yeni bir soru sor"
            color={theme.accent}
            onPress={() => router.replace('/home')}
          />
        </View>
      ) : (
        <>
          <View style={styles.answerCard}>
            <TextField
              label="Cevabın"
              hint="Sadece sonucu yaz. Örnek: 5, -2 ya da 3/4"
              value={answer}
              onChangeText={(value) => {
                setAnswer(value);
                markInteraction();
              }}
              maxLength={200}
              editable={!busy}
              onSubmitEditing={() => answer.trim() && attempt.mutate(answer.trim())}
              returnKeyType="send"
            />
            <Button
              label="Cevabımı kontrol et"
              color={theme.accent}
              loading={attempt.isPending}
              disabled={busy || answer.trim().length === 0}
              onPress={() => attempt.mutate(answer.trim())}
            />
          </View>

          {data.can_request_hint ? (
            <View style={styles.hintActions}>
              <Button
                label={hintButtonLabel(data.hints.length)}
                variant="secondary"
                color={theme.accent}
                loading={hint.isPending}
                disabled={busy}
                onPress={() => hint.mutate(hintNote.trim() ? hintNote.trim() : null)}
              />
              {showHintNote ? (
                <View style={styles.noteBox}>
                  <TextField
                    label="Neresinde takıldın? (isteğe bağlı)"
                    hint="Örnek: Eşitliğin sağ tarafında ne yapacağımı anlamadım"
                    value={hintNote}
                    onChangeText={(value) => {
                      setHintNote(value);
                      markInteraction();
                    }}
                    maxLength={500}
                    editable={!busy}
                  />
                  <Button
                    label="Mesajımla ipucu iste"
                    color={theme.accent}
                    loading={hint.isPending}
                    disabled={busy || hintNote.trim().length === 0}
                    onPress={() => hint.mutate(hintNote.trim())}
                  />
                </View>
              ) : (
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Takıldığın adımı yazarak ipucu iste"
                  disabled={busy}
                  onPress={() => {
                    setShowHintNote(true);
                    markInteraction();
                  }}
                  style={styles.askStepToggle}>
                  <Text style={[styles.askStepText, { color: theme.accent }]}>
                    💬 Takıldığım adımı yazmak istiyorum
                  </Text>
                </Pressable>
              )}
              <Button
                label={theme.emoji ? 'Bu çok zor 😕' : 'Bu çok zor'}
                variant="secondary"
                color={Colors.textMuted}
                disabled={busy}
                onPress={() => hint.mutate(FRUSTRATION_MESSAGE)}
              />
            </View>
          ) : (
            <Text style={styles.note}>
              Tüm ipuçlarını aldın. Son ipucundaki adımları kendi sorunda dene; istersen öğretmenine
              de danışabilirsin.
            </Text>
          )}
          <Button
            label="Bu soruyu bırak"
            variant="secondary"
            color={Colors.textMuted}
            disabled={busy}
            onPress={() => router.replace('/home')}
          />
        </>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  topRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: Spacing.sm,
  },
  backButton: {
    minHeight: 36,
    justifyContent: 'center',
  },
  backText: {
    fontSize: 15,
    fontWeight: '600',
  },
  readingChip: {
    minHeight: 36,
    paddingHorizontal: Spacing.sm,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
    justifyContent: 'center',
  },
  readingChipText: {
    fontSize: 13,
    color: Colors.textMuted,
  },
  questionCard: {
    borderRadius: Radius.md,
    padding: Spacing.md,
    gap: Spacing.xs,
  },
  label: {
    fontSize: 13,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  question: {
    fontWeight: '700',
    lineHeight: 28,
    color: Colors.text,
  },
  cautionBanner: {
    padding: Spacing.sm,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
  },
  cautionText: {
    fontSize: 14,
    lineHeight: 20,
    color: Colors.textMuted,
  },
  hints: {
    gap: Spacing.sm,
  },
  idleCard: {
    gap: Spacing.sm,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1.5,
    backgroundColor: Colors.surface,
  },
  idleText: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.text,
  },
  idleActions: {
    gap: Spacing.xs,
  },
  feedback: {
    fontSize: 18,
    fontWeight: '600',
    lineHeight: 25,
    color: Colors.text,
  },
  celebrationCard: {
    gap: Spacing.sm,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 2,
    backgroundColor: Colors.surface,
  },
  celebrationTitle: {
    fontSize: 20,
    fontWeight: '700',
    lineHeight: 27,
  },
  celebrationSub: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.text,
  },
  answerCard: {
    gap: Spacing.md,
    padding: Spacing.md,
    borderRadius: Radius.md,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  hintActions: {
    gap: Spacing.sm,
  },
  noteBox: {
    gap: Spacing.sm,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
  },
  askStepToggle: {
    alignSelf: 'center',
    minHeight: 36,
    justifyContent: 'center',
  },
  askStepText: {
    fontSize: 14,
    fontWeight: '600',
  },
  note: {
    fontSize: 15,
    lineHeight: 21,
    color: Colors.textMuted,
  },
});
