import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import { describeError, unwrap } from '@/api/errors';
import { Button } from '@/components/button';
import { ErrorMessage } from '@/components/error-message';
import { Screen } from '@/components/screen';
import { TextField } from '@/components/text-field';
import { Colors, Radius, Spacing } from '@/constants/theme';
import { NoticeText, type SafetyNotice, SupportCard } from '@/features/safety/support-card';
import { HintCard } from '@/features/tutoring/hint-card';
import { FRUSTRATION_MESSAGE, hintButtonLabel } from '@/features/tutoring/ladder';
import { LadderProgress } from '@/features/tutoring/ladder-progress';
import { useChildTheme } from '@/features/tutoring/use-child-theme';

type Feedback = { tone: 'success' | 'info'; text: string };

export default function ProblemScreen() {
  const { id, notice: initialNotice } = useLocalSearchParams<{ id: string; notice?: string }>();
  const theme = useChildTheme();
  const queryClient = useQueryClient();
  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [notice, setNotice] = useState<string | null>(initialNotice ?? null);
  const [safety, setSafety] = useState<SafetyNotice | null>(null);

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

  const hint = useMutation({
    mutationFn: (message: string | null) =>
      unwrap(
        api.POST('/v1/problems/{problem_id}/hints', {
          params: { path: { problem_id: id } },
          body: { message },
        }),
      ),
    onSuccess: (result) => {
      setFeedback(null);
      setSafety(result.safety ?? null);
      setNotice(result.notice ?? null);
      return refresh();
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

  return (
    <Screen>
      <View style={[styles.questionCard, { backgroundColor: theme.accentSoft }]}>
        <Text style={[styles.label, { color: theme.accent }]}>
          {data.topic ? `Sorun · ${data.topic}` : 'Sorun'}
        </Text>
        <Text style={[styles.question, { fontSize: 20 * theme.fontScale }]}>{data.text}</Text>
      </View>

      {notice ? <NoticeText text={notice} /> : null}
      {safety ? <SupportCard notice={safety} /> : null}

      <LadderProgress
        current={data.current_hint_level ?? null}
        maxLevel={data.max_hint_level}
        theme={theme}
      />

      {data.hints.length > 0 ? (
        <View style={styles.hints} accessibilityLiveRegion="polite">
          {data.hints.map((item, index) => (
            <HintCard
              key={item.id}
              level={item.level}
              levelName={item.level_name}
              text={item.text}
              latest={index === latestIndex}
              theme={theme}
            />
          ))}
        </View>
      ) : null}

      {feedback ? (
        <Text
          role="status"
          accessibilityLiveRegion="polite"
          style={[styles.feedback, feedback.tone === 'success' && { color: theme.accent }]}>
          {feedback.tone === 'success' && theme.emoji ? '🎉 ' : ''}
          {feedback.text}
        </Text>
      ) : null}
      <ErrorMessage message={actionError ? describeError(actionError) : null} />

      {solved ? (
        <Button
          label="Yeni bir soru sor"
          color={theme.accent}
          onPress={() => router.replace('/home')}
        />
      ) : (
        <>
          <View style={styles.answerCard}>
            <TextField
              label="Cevabın"
              hint="Sadece sonucu yaz. Örnek: 5, -2 ya da 3/4"
              value={answer}
              onChangeText={setAnswer}
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
                onPress={() => hint.mutate(null)}
              />
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
  hints: {
    gap: Spacing.sm,
  },
  feedback: {
    fontSize: 18,
    fontWeight: '600',
    lineHeight: 25,
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
  note: {
    fontSize: 15,
    lineHeight: 21,
    color: Colors.textMuted,
  },
});
