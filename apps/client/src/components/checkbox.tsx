import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Colors, Spacing } from '@/constants/theme';

type Props = {
  label: string;
  description?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  color?: string;
};

export function Checkbox({ label, description, checked, onChange, color = Colors.guardian }: Props) {
  return (
    <Pressable
      accessibilityRole="checkbox"
      accessibilityLabel={label}
      aria-checked={checked}
      onPress={() => onChange(!checked)}
      style={styles.row}>
      <View style={[styles.box, { borderColor: color }, checked && { backgroundColor: color }]}>
        {checked ? <Text style={styles.tick}>✓</Text> : null}
      </View>
      <View style={styles.texts}>
        <Text style={styles.label}>{label}</Text>
        {description ? <Text style={styles.description}>{description}</Text> : null}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: Spacing.md,
    paddingVertical: Spacing.sm,
  },
  box: {
    width: 28,
    height: 28,
    borderWidth: 2,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tick: {
    color: Colors.onPrimary,
    fontSize: 18,
    fontWeight: '700',
  },
  texts: {
    flex: 1,
    gap: 2,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
  },
  description: {
    fontSize: 14,
    lineHeight: 20,
    color: Colors.textMuted,
  },
});
