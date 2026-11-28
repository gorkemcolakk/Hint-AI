import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { MathText } from '@/components/math-text';
import { Colors, Radius, Spacing } from '@/constants/theme';
import type { ChildTheme } from '@/features/tutoring/ladder';
import { submitHintFeedback } from '@/features/tutoring/stream-hint';

type Props = {
  id?: string;
  level: number;
  levelName: string;
  text: string;
  latest: boolean;
  theme: ChildTheme;
  comfortableReading?: boolean;
  streaming?: boolean;
  canRequestClarification?: boolean;
  onRequestClarification?: () => void;
};

export function HintCard({
  id,
  level,
  levelName,
  text,
  latest,
  theme,
  comfortableReading = false,
  streaming = false,
  canRequestClarification = false,
  onRequestClarification,
}: Props) {
  const [feedback, setFeedback] = useState<'helpful' | 'unclear' | null>(null);

  function handleFeedback(choice: 'helpful' | 'unclear') {
    setFeedback(choice);
    if (id) {
      void submitHintFeedback(id, choice === 'helpful');
    }
    if (choice === 'unclear' && canRequestClarification && onRequestClarification) {
      onRequestClarification();
    }
  }

  return (
    <View
      accessible
      accessibilityLabel={`İpucu, basamak ${level + 1}, ${levelName}: ${text}`}
      style={[
        styles.card,
        latest ? { borderColor: theme.accent, backgroundColor: theme.accentSoft } : styles.previous,
      ]}>
      <Text style={[styles.badge, { color: theme.accent }]}>
        {theme.emoji && latest ? '💡 ' : ''}
        {levelName}
        {streaming ? ' · yazılıyor…' : ''}
      </Text>
      <MathText
        comfortableReading={comfortableReading}
        style={[
          styles.text,
          { fontSize: 17 * theme.fontScale * (comfortableReading ? 1.08 : 1) },
          !latest && styles.mutedText,
        ]}>
        {text}
      </MathText>

      {latest && !streaming && id ? (
        <View style={styles.feedbackRow}>
          {feedback === 'helpful' ? (
            <Text style={styles.feedbackAck}>
              {theme.emoji ? '🙌 ' : ''}İşine yaradığına sevindim! Şimdi cevabını deneyebilirsin.
            </Text>
          ) : feedback === 'unclear' ? (
            <Text style={styles.feedbackAck}>
              Not aldım! Biraz daha açık bir ipucu için devam edebiliriz.
            </Text>
          ) : (
            <>
              <Text style={styles.feedbackPrompt}>Bu ipucu yardımcı oldu mu?</Text>
              <View style={styles.feedbackButtons}>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Bu ipucu işime yaradı"
                  onPress={() => handleFeedback('helpful')}
                  style={({ pressed }) => [
                    styles.pill,
                    { borderColor: theme.accent },
                    pressed && styles.pressed,
                  ]}>
                  <Text style={[styles.pillText, { color: theme.accent }]}>
                    {theme.emoji ? '👍 ' : ''}İşime yaradı
                  </Text>
                </Pressable>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Bu ipucunu tam anlamadım"
                  onPress={() => handleFeedback('unclear')}
                  style={({ pressed }) => [styles.pill, pressed && styles.pressed]}>
                  <Text style={styles.pillMutedText}>
                    {theme.emoji ? '🤔 ' : ''}Tam anlamadım
                  </Text>
                </Pressable>
              </View>
            </>
          )}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderWidth: 2,
    borderRadius: Radius.md,
    padding: Spacing.md,
    gap: Spacing.xs,
  },
  previous: {
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
  },
  badge: {
    fontSize: 13,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  text: {
    lineHeight: 25,
    color: Colors.text,
  },
  mutedText: {
    color: Colors.textMuted,
  },
  feedbackRow: {
    marginTop: Spacing.xs,
    paddingTop: Spacing.xs,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    gap: Spacing.xs,
  },
  feedbackPrompt: {
    fontSize: 13,
    color: Colors.textMuted,
  },
  feedbackButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.xs,
  },
  pill: {
    minHeight: 36,
    paddingHorizontal: Spacing.sm,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
    justifyContent: 'center',
  },
  pillText: {
    fontSize: 13,
    fontWeight: '600',
  },
  pillMutedText: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textMuted,
  },
  feedbackAck: {
    fontSize: 13,
    color: Colors.textMuted,
    fontStyle: 'italic',
  },
  pressed: {
    opacity: 0.8,
  },
});
