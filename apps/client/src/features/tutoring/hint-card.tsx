import { StyleSheet, Text, View } from 'react-native';

import { Colors, Radius, Spacing } from '@/constants/theme';
import type { ChildTheme } from '@/features/tutoring/ladder';

type Props = {
  level: number;
  levelName: string;
  text: string;
  latest: boolean;
  theme: ChildTheme;
};

export function HintCard({ level, levelName, text, latest, theme }: Props) {
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
      </Text>
      <Text style={[styles.text, { fontSize: 17 * theme.fontScale }, !latest && styles.mutedText]}>
        {text}
      </Text>
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
});
