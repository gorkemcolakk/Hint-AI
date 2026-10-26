import { StyleSheet, Text, TextInput, type TextInputProps, View } from 'react-native';

import { Colors, Radius, Spacing } from '@/constants/theme';

type Props = TextInputProps & {
  label: string;
  hint?: string;
};

export function TextField({ label, hint, style, ...inputProps }: Props) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        accessibilityHint={hint}
        placeholderTextColor={Colors.textMuted}
        style={[styles.input, style]}
        {...inputProps}
      />
      {hint ? <Text style={styles.hint}>{hint}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  field: {
    gap: Spacing.xs,
  },
  label: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.text,
  },
  input: {
    minHeight: 48,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    backgroundColor: Colors.surface,
    paddingHorizontal: Spacing.md,
    fontSize: 16,
    color: Colors.text,
  },
  hint: {
    fontSize: 13,
    color: Colors.textMuted,
  },
});
