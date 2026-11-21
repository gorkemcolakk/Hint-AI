import { ScrollView, StyleSheet, Text, View } from 'react-native';

import type { components } from '@/api/schema';
import { Colors, Spacing } from '@/constants/theme';
import { cellLabel, HEAT_LEGEND, HEAT_STEPS, heatStep } from '@/features/classrooms/heat';

type Heatmap = components['schemas']['Heatmap'];

const TOPIC_WIDTH = 150;
const CELL_WIDTH = 64;
const CELL_HEIGHT = 40;

/**
 * Konu × öğrenci ısı haritası: hücre = o öğrencinin o konudaki soru başına ortalama ipucu.
 * Koyulaştıkça daha çok ipucu (daha çok zorlanma). Veri olmayan hücre kesikli çerçeveli boş.
 * Aynı bilgi ekran okuyucu için her hücrenin etiketinde ve öğrenci tablosunda da var.
 */
export function HeatmapGrid({ heatmap }: { heatmap: Heatmap }) {
  const cells = new Map(heatmap.cells.map((cell) => [`${cell.topic}|${cell.child_id}`, cell]));
  const students = heatmap.students.filter((student) => student.problems > 0);

  return (
    <View style={styles.wrapper}>
      <ScrollView horizontal showsHorizontalScrollIndicator>
        <View>
          <View style={styles.row}>
            <View style={styles.topicCell} />
            {students.map((student) => (
              <Text key={student.child_id} style={styles.columnHead} numberOfLines={1}>
                {student.nickname}
              </Text>
            ))}
          </View>
          {heatmap.topics.map((topic) => (
            <View key={topic.topic} style={styles.row}>
              <View style={styles.topicCell}>
                <Text style={styles.topicText} numberOfLines={2}>
                  {topic.topic}
                </Text>
              </View>
              {students.map((student) => {
                const cell = cells.get(`${topic.topic}|${student.child_id}`);
                const label = cellLabel(topic.topic, student.nickname, cell);
                if (!cell) {
                  return (
                    <View
                      key={student.child_id}
                      accessible
                      accessibilityLabel={label}
                      style={[styles.cell, styles.emptyCell]}>
                      <Text style={styles.emptyText}>–</Text>
                    </View>
                  );
                }
                const step = heatStep(cell.avg_hints);
                return (
                  <View
                    key={student.child_id}
                    accessible
                    accessibilityLabel={label}
                    style={[styles.cell, { backgroundColor: step.color }]}>
                    <Text style={[styles.cellText, { color: step.text }]}>
                      {cell.avg_hints.toLocaleString('tr-TR', { maximumFractionDigits: 1 })}
                    </Text>
                  </View>
                );
              })}
            </View>
          ))}
        </View>
      </ScrollView>

      <View
        accessible
        accessibilityLabel="Renk açıklaması: koyulaştıkça soru başına daha çok ipucu">
        <Text style={styles.legendTitle}>Soru başına ortalama ipucu</Text>
        <View style={styles.legendRow}>
          {HEAT_STEPS.map((step, index) => (
            <View key={step.color} style={styles.legendItem}>
              <View style={[styles.legendSwatch, { backgroundColor: step.color }]} />
              <Text style={styles.legendText}>{HEAT_LEGEND[index]}</Text>
            </View>
          ))}
        </View>
        <Text style={styles.legendNote}>
          Açık: kendi başına ilerliyor · Koyu: çok ipucu gerekiyor
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: Spacing.md },
  row: { flexDirection: 'row', alignItems: 'center', gap: 2, marginBottom: 2 },
  topicCell: { width: TOPIC_WIDTH, paddingRight: Spacing.sm, justifyContent: 'center' },
  topicText: { fontSize: 14, color: Colors.text },
  columnHead: {
    width: CELL_WIDTH,
    fontSize: 13,
    fontWeight: '600',
    textAlign: 'center',
    color: Colors.textMuted,
  },
  cell: {
    width: CELL_WIDTH,
    height: CELL_HEIGHT,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyCell: { borderStyle: 'dashed', backgroundColor: Colors.surface },
  emptyText: { fontSize: 14, color: Colors.textMuted },
  cellText: { fontSize: 14, fontWeight: '600', fontVariant: ['tabular-nums'] },
  legendTitle: { fontSize: 13, fontWeight: '600', color: Colors.textMuted },
  legendRow: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm, marginTop: Spacing.xs },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: Spacing.xs },
  legendSwatch: {
    width: 16,
    height: 16,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  legendText: { fontSize: 13, color: Colors.text },
  legendNote: { fontSize: 13, color: Colors.textMuted, marginTop: Spacing.xs },
});
