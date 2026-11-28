import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { ApiError } from '@/api/errors';
import { Colors, Radius, Spacing } from '@/constants/theme';
import type { ChildTheme } from '@/features/tutoring/ladder';

const SELF_CHECK_STEPS = [
  'Soruda hangi sayılar verilmiş ve benden tam olarak ne isteniyor?',
  'Verilenleri küçük bir şekil, tablo ya da sayı doğrusuyla çizebilir miyim?',
  'Daha küçük ve kolay sayılar koyup aynı yöntemi deneyebilir miyim?',
  'Yaptığım işlemleri baştan sona tersinden kontrol ettim mi?',
] as const;

export function isQuotaError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 429;
}

/**
 * Günlük kota dolduğunda çocuğu çaresiz bırakmayan sıfır maliyetli
 * kendi kendine kontrol listesi (Bölüm 5.5).
 */
export function QuotaChecklistCard({ theme }: { theme: ChildTheme }) {
  const [checked, setChecked] = useState<Record<number, boolean>>({});

  function toggle(index: number) {
    setChecked((prev) => ({ ...prev, [index]: !prev[index] }));
  }

  return (
    <View
      role="region"
      accessibilityLabel="Kendi kendine kontrol listesi"
      style={[styles.card, { borderColor: theme.accent }]}>
      <Text style={[styles.title, { color: theme.accent }]}>
        {theme.emoji ? '🧭 ' : ''}Bugünkü yapay zekâ hakkın doldu
      </Text>
      <Text style={styles.body}>
        Yarın kaldığımız yerden yeni ipuçlarıyla devam edebiliriz. Şimdi soruyu kendi başına
        çözmek için bu 4 adımı tek tek dene:
      </Text>
      <View style={styles.list}>
        {SELF_CHECK_STEPS.map((step, index) => {
          const done = Boolean(checked[index]);
          return (
            <Pressable
              key={step}
              accessibilityRole="checkbox"
              accessibilityLabel={step}
              accessibilityState={{ checked: done }}
              aria-checked={done}
              onPress={() => toggle(index)}
              style={styles.item}>
              <View
                style={[
                  styles.box,
                  done && { backgroundColor: theme.accent, borderColor: theme.accent },
                ]}>
                {done ? <Text style={styles.check}>✓</Text> : null}
              </View>
              <Text style={[styles.stepText, done && styles.stepDone]}>{step}</Text>
            </Pressable>
          );
        })}
      </View>
      <Text style={styles.footer}>
        Takıldığın yeri defterine not alırsan yarın birlikte bakabiliriz veya öğretmenine
        sorabilirsin.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: Spacing.sm,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 2,
    backgroundColor: Colors.surface,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
  },
  body: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.text,
  },
  list: {
    gap: Spacing.sm,
    marginVertical: Spacing.xs,
  },
  item: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: Spacing.sm,
    minHeight: 44,
    paddingVertical: Spacing.xs,
  },
  box: {
    width: 24,
    height: 24,
    marginTop: 2,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  check: {
    color: Colors.onPrimary,
    fontWeight: '800',
    fontSize: 14,
  },
  stepText: {
    flex: 1,
    fontSize: 15,
    lineHeight: 22,
    color: Colors.text,
  },
  stepDone: {
    color: Colors.textMuted,
    textDecorationLine: 'line-through',
  },
  footer: {
    fontSize: 13,
    lineHeight: 19,
    color: Colors.textMuted,
  },
});
