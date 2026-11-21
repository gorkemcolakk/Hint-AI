import { useQuery } from '@tanstack/react-query';
import { useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  Platform,
  Pressable,
  Share,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { api } from '@/api/client';
import { describeError, unwrap } from '@/api/errors';
import { Button } from '@/components/button';
import { ErrorMessage } from '@/components/error-message';
import { Screen } from '@/components/screen';
import { Colors, Radius, Spacing } from '@/constants/theme';
import { formatJoinCode, struggleCaption } from '@/features/classrooms/heat';
import { HeatmapGrid } from '@/features/classrooms/heatmap-grid';
import { formatDecimal } from '@/features/progress/format';

const PERIODS = [
  { days: 7, label: '7 gün' },
  { days: 30, label: '30 gün' },
  { days: 90, label: '90 gün' },
] as const;

export default function ClassroomScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [days, setDays] = useState<number>(30);
  const heatmap = useQuery({
    queryKey: ['classrooms', id, 'heatmap', days],
    queryFn: () =>
      unwrap(
        api.GET('/v1/classrooms/{classroom_id}/heatmap', {
          params: { path: { classroom_id: id }, query: { days } },
        }),
      ),
    enabled: Boolean(id),
  });

  if (heatmap.isPending) {
    return (
      <Screen hasHeader>
        <ActivityIndicator color={Colors.teacher} />
      </Screen>
    );
  }
  if (heatmap.isError) {
    return (
      <Screen hasHeader>
        <ErrorMessage message={describeError(heatmap.error)} />
      </Screen>
    );
  }

  const data = heatmap.data;
  const code = data.classroom.join_code;
  const struggling = data.topics.filter((topic) => topic.struggling > 0);
  const shareText = `Hint.ai'de "${data.classroom.name}" sınıfına katılmak için davet kodu: ${code}. Ebeveyn panelinde çocuğunuzun profiline girip bu kodu yazın.`;

  return (
    <Screen hasHeader>
      <View style={styles.headerCard}>
        <Text accessibilityRole="header" style={styles.title}>
          {data.classroom.name}
        </Text>
        <Text style={styles.meta}>
          {data.classroom.student_count} öğrenci (veli onaylı)
          {data.classroom.grade ? ` · ${data.classroom.grade}. sınıf` : ''}
        </Text>
        <View style={styles.codeBox} accessible accessibilityLabel={`Davet kodu ${code}`}>
          <Text style={styles.codeLabel}>Davet kodu</Text>
          <Text selectable style={styles.code}>
            {formatJoinCode(code)}
          </Text>
          <Text style={styles.codeNote}>
            Velilerle paylaş. Veli kodu çocuğunun profiline girip onay verdiğinde öğrenci sınıfına
            eklenir. Soru metinlerini ve güvenlik uyarılarını göremezsin; yalnızca konu bazında özet
            görürsün.
          </Text>
          {Platform.OS !== 'web' ? (
            <Button
              label="Kodu paylaş"
              variant="secondary"
              color={Colors.teacher}
              onPress={() => void Share.share({ message: shareText })}
            />
          ) : null}
        </View>
      </View>

      <View style={styles.headerRow}>
        <Text accessibilityRole="header" style={styles.section}>
          Kazanım ısı haritası
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

      {data.cells.length === 0 ? (
        <Text style={styles.empty}>
          Bu dönemde sınıfta çalışılmış soru yok. Veliler davet kodunu girip öğrenciler soru
          çözdükçe harita dolacak.
        </Text>
      ) : (
        <>
          <View style={styles.card}>
            <HeatmapGrid heatmap={data} />
          </View>

          {struggling.length > 0 ? (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Sınıfın zorlandığı konular</Text>
              {struggling.map((topic) => (
                <View key={topic.topic} style={styles.topicRow}>
                  <Text style={styles.topicName}>{topic.topic}</Text>
                  <Text style={styles.meta}>{struggleCaption(topic)}</Text>
                </View>
              ))}
              <Text style={styles.note}>
                Zorlanma: ortalama 3 ve üzeri ipucu kullanma ya da hiç çözememe.
              </Text>
            </View>
          ) : null}

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Öğrenciler</Text>
            <View style={[styles.tableRow, styles.tableHead]}>
              <Text style={[styles.colName, styles.th]}>Öğrenci</Text>
              <Text style={[styles.colNum, styles.th]}>Soru</Text>
              <Text style={[styles.colNum, styles.th]}>Çözülen</Text>
              <Text style={[styles.colNum, styles.th]}>Ort. ipucu</Text>
              <Text style={[styles.colNum, styles.th]}>Cevap isteme</Text>
            </View>
            {data.students.map((student) => (
              <View
                key={student.child_id}
                accessible
                accessibilityLabel={`${student.nickname}: ${student.problems} soru, ${student.solved} çözüldü, ortalama ${formatDecimal(student.avg_hints)} ipucu, ${student.answer_requests} kez cevap istedi`}
                style={styles.tableRow}>
                <Text style={styles.colName} numberOfLines={1}>
                  {student.nickname}
                </Text>
                <Text style={styles.colNum}>{student.problems}</Text>
                <Text style={styles.colNum}>{student.solved}</Text>
                <Text style={styles.colNum}>{formatDecimal(student.avg_hints)}</Text>
                <Text style={styles.colNum}>{student.answer_requests}</Text>
              </View>
            ))}
            <Text style={styles.note}>
              Cevap isteme: öğrencinin cevabı doğrudan istediği mesaj sayısı; uygulama cevap
              vermedi, ipucuyla devam etti.
            </Text>
          </View>
          <Text style={styles.note}>
            Konu adları yapay zekâ tarafından belirleniyor; MEB kazanım kodlarına eşleme henüz yok.
          </Text>
        </>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  headerCard: {
    gap: Spacing.sm,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
  },
  title: { fontSize: 24, fontWeight: '700', color: Colors.text },
  meta: { fontSize: 14, color: Colors.textMuted },
  codeBox: {
    gap: Spacing.xs,
    padding: Spacing.md,
    borderRadius: Radius.md,
    backgroundColor: '#F3EEF8',
  },
  codeLabel: { fontSize: 13, fontWeight: '600', color: Colors.teacher },
  code: {
    fontSize: 32,
    fontWeight: '800',
    letterSpacing: 4,
    color: Colors.text,
    fontVariant: ['tabular-nums'],
  },
  codeNote: { fontSize: 13, lineHeight: 18, color: Colors.text },
  headerRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: Spacing.sm,
  },
  section: { fontSize: 20, fontWeight: '700', color: Colors.text },
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
  periodSelected: { backgroundColor: Colors.teacher },
  periodText: { fontSize: 14, color: Colors.text },
  periodTextSelected: { color: Colors.onPrimary, fontWeight: '600' },
  empty: { fontSize: 15, lineHeight: 21, color: Colors.textMuted },
  card: {
    gap: Spacing.md,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
  },
  cardTitle: { fontSize: 16, fontWeight: '700', color: Colors.text },
  topicRow: { gap: 2 },
  topicName: { fontSize: 15, fontWeight: '600', color: Colors.text },
  note: { fontSize: 13, lineHeight: 18, color: Colors.textMuted },
  tableRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: Spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  tableHead: { borderBottomWidth: 2 },
  th: { fontWeight: '700', color: Colors.textMuted, fontSize: 12 },
  colName: { flex: 2, fontSize: 14, color: Colors.text },
  colNum: {
    flex: 1,
    fontSize: 14,
    textAlign: 'right',
    color: Colors.text,
    fontVariant: ['tabular-nums'],
  },
});
