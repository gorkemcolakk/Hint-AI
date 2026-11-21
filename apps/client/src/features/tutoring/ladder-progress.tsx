import { StyleSheet, Text, View } from 'react-native';

import { Colors, Spacing } from '@/constants/theme';
import { type ChildTheme, ladderCaption, ladderSteps } from '@/features/tutoring/ladder';

type Props = { current: number | null; maxLevel: number; theme: ChildTheme };

/** İpucu merdiveninde kaçıncı basamakta olunduğunu gösterir (L0 → maxLevel). */
export function LadderProgress({ current, maxLevel, theme }: Props) {
  const steps = ladderSteps(current, maxLevel);
  const caption = ladderCaption(current, maxLevel);
  return (
    <View
      accessible
      accessibilityRole="progressbar"
      accessibilityLabel={caption}
      accessibilityValue={{
        min: 0,
        max: maxLevel + 1,
        now: current === null ? 0 : current + 1,
      }}
      style={styles.wrapper}>
      <View style={styles.row}>
        {steps.map((step, level) => (
          <View
            key={level}
            style={[
              styles.step,
              step === 'upcoming' && styles.upcoming,
              step !== 'upcoming' && { backgroundColor: theme.accent },
              step === 'done' && styles.done,
            ]}
          />
        ))}
      </View>
      <Text style={styles.caption}>{caption}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: Spacing.xs },
  row: { flexDirection: 'row', gap: Spacing.xs },
  step: { flex: 1, height: 8, borderRadius: 4 },
  upcoming: { backgroundColor: Colors.border },
  done: { opacity: 0.45 },
  caption: { fontSize: 14, color: Colors.textMuted },
});
