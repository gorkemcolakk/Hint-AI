import { ActivityIndicator, Pressable, StyleSheet, Text } from 'react-native';

import { Colors, Radius, Spacing } from '@/constants/theme';

type Props = {
  label: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary';
  color?: string;
  disabled?: boolean;
  loading?: boolean;
};

export function Button({
  label,
  onPress,
  variant = 'primary',
  color = Colors.guardian,
  disabled = false,
  loading = false,
}: Props) {
  const inactive = disabled || loading;
  const primary = variant === 'primary';
  const contentColor = primary ? Colors.onPrimary : color;

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      aria-disabled={inactive}
      aria-busy={loading}
      disabled={inactive}
      onPress={onPress}
      style={({ pressed }) => [
        styles.base,
        primary ? { backgroundColor: color } : { borderColor: color, borderWidth: 2 },
        inactive && styles.inactive,
        pressed && styles.pressed,
      ]}>
      {loading ? (
        <ActivityIndicator color={contentColor} />
      ) : (
        <Text style={[styles.label, { color: contentColor }]}>{label}</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    minHeight: 52,
    borderRadius: Radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: Spacing.lg,
  },
  label: {
    fontSize: 17,
    fontWeight: '600',
  },
  inactive: {
    opacity: 0.5,
  },
  pressed: {
    opacity: 0.85,
  },
});
