import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import { describeError, unwrap } from '@/api/errors';
import { ErrorMessage } from '@/components/error-message';
import { Colors, Radius, Spacing } from '@/constants/theme';
import {
  formatDecimal,
  formatShortDate,
  hintsCaption,
  independenceCaption,
} from '@/features/progress/format';
import { MeterRow, StatTile } from '@/features/progress/summary-parts';

const PERIODS = [
  { days: 7, label: 'Son 7 gün' },
  { days: 30, label: 'Son 30 gün' },
] as const;

/** Ebeveynin gördüğü dönem özeti (A4). Varsayılan gizlilikte soru metni gösterilmez. */
export function ChildSummary({ childId }: { childId: string }) {
  const [days, setDays] = useState<number>(7);
  const summary = useQuery({
    queryKey: ['children', childId, 'summary', days],
    queryFn: () =>
      unwrap(
        api.GET('/v1/children/{child_id}/summary', {
          params: { path: { child_id: childId }, query: { days } },
        }),
      ),
  });

  return (
    <View style={styles.section}>
      <View style={styles.headerRow}>
        <Text accessibilityRole="header" style={styles.title}>
          İlerleme özeti
        </Text>
        <View accessibilityRole="tablist" style={styles.periods}>
          {PERIODS.map((period) => {
            const selected = period.days === days;
            return (
              <Pressable
                key={period.days}
                accessibilityRole="tab"
                accessibilityState={{ selected }}
                onPress={() => setDays(period.days)}
                style={[styles.period, selected && styles.periodSelected]}>
                <Text style={[styles.periodText, selected && styles.periodTextSelected]}>
                  {period.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      {summary.isPending ? <ActivityIndicator color={Colors.guardian} /> : null}
      <ErrorMessage message={summary.isError ? describeError(summary.error) : null} />

      {summary.data ? (
        <>
          {summary.data.alerts.map((alert, index) => (
            <View key={index} role="alert" style={styles.alert}>
              <Text style={styles.alertTitle}>
                ⚠ Güvenlik uyarısı · {formatShortDate(alert.created_at)}
              </Text>
              <Text style={styles.alertBody}>{alert.title}</Text>
              <Text style={styles.alertGuidance}>{alert.guidance}</Text>
            </View>
          ))}

          <View style={styles.tiles}>
            <StatTile
              label="Çözülen soru"
              value={String(summary.data.problems_solved)}
              caption={`${summary.data.problems_started} soruya başladı; cevap hiç gösterilmedi`}
            />
            <StatTile
              label="İpucusuz çözülen"
              value={String(summary.data.solved_without_hints)}
              caption={independenceCaption(
                summary.data.problems_solved,
                summary.data.solved_without_hints,
              )}
            />
            <StatTile
              label="Ortalama ipucu"
              value={formatDecimal(summary.data.avg_hints_per_solved)}
              caption={hintsCaption(summary.data.avg_hints_per_solved)}
            />
          </View>

          {summary.data.topics.length > 0 ? (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Konular</Text>
              {summary.data.topics.map((topic) => (
                <MeterRow
                  key={topic.topic}
                  name={topic.topic}
                  value={topic.solved}
                  total={topic.problems}
                />
              ))}
            </View>
          ) : (
            <Text style={styles.empty}>Bu dönemde henüz soru çalışılmadı.</Text>
          )}

          {summary.data.recent.length > 0 ? (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Son sorular</Text>
              {summary.data.recent.map((item) => (
                <View
                  key={item.id}
                  accessible
                  accessibilityLabel={`${formatShortDate(item.created_at)}, ${item.topic}, ${
                    item.solved ? 'çözüldü' : 'devam ediyor'
                  }, ${item.hints_used} ipucu, ${item.attempts} deneme`}
                  style={styles.recentRow}>
                  <View style={styles.recentMain}>
                    <Text style={styles.recentTopic} numberOfLines={1}>
                      {item.topic}
                    </Text>
                    {item.text ? (
                      <Text style={styles.recentText} numberOfLines={2}>
                        {item.text}
                      </Text>
                    ) : null}
                    <Text style={styles.recentMeta}>
                      {formatShortDate(item.created_at)} · {item.hints_used} ipucu · {item.attempts}{' '}
                      deneme
                    </Text>
                  </View>
                  <Text style={[styles.badge, item.solved ? styles.badgeDone : styles.badgeOpen]}>
                    {item.solved ? '✓ Çözüldü' : 'Devam ediyor'}
                  </Text>
                </View>
              ))}
              {!summary.data.shows_problem_text ? (
                <Text style={styles.privacy}>
                  Gizlilik ayarı gereği soru metinleri değil, yalnızca konular gösteriliyor.
                </Text>
              ) : null}
            </View>
          ) : null}

          {Object.keys(summary.data.flags).length > 0 || summary.data.answer_requests > 0 ? (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Diğer notlar</Text>
              {Object.entries(summary.data.flags).map(([label, count]) => (
                <Text key={label} style={styles.note}>
                  {label}: {count} kez (uygulama konuyu nazikçe matematiğe yönlendirdi)
                </Text>
              ))}
              {summary.data.answer_requests > 0 ? (
                <Text style={styles.note}>
                  Cevabı doğrudan isteme: {summary.data.answer_requests} kez (cevap verilmedi,
                  ipucuyla devam edildi)
                </Text>
              ) : null}
            </View>
          ) : null}
        </>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  section: { gap: Spacing.md },
  headerRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: Spacing.sm,
  },
  title: { fontSize: 20, fontWeight: '700', color: Colors.text },
  periods: {
    flexDirection: 'row',
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    overflow: 'hidden',
  },
  period: {
    minHeight: 40,
    paddingHorizontal: Spacing.md,
    justifyContent: 'center',
    backgroundColor: Colors.surface,
  },
  periodSelected: { backgroundColor: Colors.guardian },
  periodText: { fontSize: 14, color: Colors.text },
  periodTextSelected: { color: Colors.onPrimary, fontWeight: '600' },
  alert: {
    gap: Spacing.xs,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 2,
    borderColor: Colors.danger,
    backgroundColor: '#FDF2F1',
  },
  alertTitle: { fontSize: 14, fontWeight: '700', color: Colors.danger },
  alertBody: { fontSize: 16, fontWeight: '600', color: Colors.text },
  alertGuidance: { fontSize: 14, lineHeight: 20, color: Colors.text },
  tiles: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  card: {
    gap: Spacing.md,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
  },
  cardTitle: { fontSize: 16, fontWeight: '700', color: Colors.text },
  empty: { fontSize: 15, color: Colors.textMuted },
  recentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    paddingBottom: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  recentMain: { flex: 1, gap: 2 },
  recentTopic: { fontSize: 15, fontWeight: '600', color: Colors.text },
  recentText: { fontSize: 14, color: Colors.text },
  recentMeta: { fontSize: 13, color: Colors.textMuted },
  badge: {
    fontSize: 13,
    fontWeight: '600',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: Radius.md,
    overflow: 'hidden',
  },
  badgeDone: { color: Colors.child, backgroundColor: '#E6F4F1' },
  badgeOpen: { color: Colors.textMuted, backgroundColor: Colors.background },
  privacy: { fontSize: 13, lineHeight: 18, color: Colors.textMuted },
  note: { fontSize: 14, lineHeight: 20, color: Colors.text },
});
