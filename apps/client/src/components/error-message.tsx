import { StyleSheet, Text } from 'react-native';

import { Colors } from '@/constants/theme';

export function ErrorMessage({ message }: { message: string | null }) {
  if (!message) {
    return null;
  }
  return (
    <Text role="alert" accessibilityLiveRegion="polite" style={styles.error}>
      {message}
    </Text>
  );
}

const styles = StyleSheet.create({
  error: {
    fontSize: 15,
    lineHeight: 21,
    color: Colors.danger,
  },
});
