import type { ReactNode } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Colors, MaxContentWidth, Spacing } from '@/constants/theme';

type Props = {
  title?: string;
  subtitle?: string;
  /** Ekranın üstünde navigasyon başlığı varsa üst güvenli alanı başlık zaten karşılar. */
  hasHeader?: boolean;
  children: ReactNode;
};

/** Tüm ekranların ortak iskeleti: güvenli alan, kaydırma ve ortalanmış içerik. */
export function Screen({ title, subtitle, hasHeader = false, children }: Props) {
  return (
    <SafeAreaView
      style={styles.safeArea}
      edges={hasHeader ? ['bottom', 'left', 'right'] : ['top', 'bottom', 'left', 'right']}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.content}>
          {title ? (
            <Text accessibilityRole="header" style={styles.title}>
              {title}
            </Text>
          ) : null}
          {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
          {children}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scroll: {
    flexGrow: 1,
    alignItems: 'center',
    padding: Spacing.lg,
  },
  content: {
    width: '100%',
    maxWidth: MaxContentWidth,
    gap: Spacing.md,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.text,
  },
  subtitle: {
    fontSize: 16,
    lineHeight: 22,
    color: Colors.textMuted,
  },
});
