import { StyleSheet, Text, View } from 'react-native';

import { Colors, Radius, Spacing } from '@/constants/theme';
import { meterLabel, meterRatio } from '@/features/progress/format';

// Meter: dolgu ebeveyn rengi, iz aynı rengin açık tonu (aynı aileden; dataviz "meter" kuralı).
const METER_FILL = Colors.guardian;
const METER_TRACK = '#DCE6F3';

/** Stat tile: etiket · değer · açıklama. Değer metin renginde; renk yalnızca vurgu çizgisinde. */
export function StatTile({
  label,
  value,
  caption,
}: {
  label: string;
  value: string;
  caption: string;
}) {
  return (
    <View accessible accessibilityLabel={`${label}: ${value}. ${caption}`} style={styles.tile}>
      <Text style={styles.tileLabel}>{label}</Text>
      <Text style={styles.tileValue}>{value}</Text>
      <Text style={styles.tileCaption}>{caption}</Text>
    </View>
  );
}

/** Meter listesi satırı: ad, çubuk ve rakam aynı hizada. */
export function MeterRow({ name, value, total }: { name: string; value: number; total: number }) {
  const ratio = meterRatio(value, total);
  return (
    <View accessible accessibilityLabel={meterLabel(name, value, total)} style={styles.meterRow}>
      <View style={styles.meterHead}>
        <Text style={styles.meterName} numberOfLines={1}>
          {name}
        </Text>
        <Text style={styles.meterFigure}>
          {value}/{total} çözüldü
        </Text>
      </View>
      <View style={styles.track}>
        {ratio > 0 ? <View style={[styles.fill, { width: `${ratio * 100}%` }]} /> : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  tile: {
    flexGrow: 1,
    flexBasis: 150,
    gap: 2,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    borderTopWidth: 3,
    borderTopColor: Colors.guardian,
    backgroundColor: Colors.surface,
  },
  tileLabel: {
    fontSize: 14,
    color: Colors.textMuted,
  },
  tileValue: {
    fontSize: 30,
    fontWeight: '600',
    color: Colors.text,
    fontVariant: ['tabular-nums'],
  },
  tileCaption: {
    fontSize: 13,
    lineHeight: 18,
    color: Colors.textMuted,
  },
  meterRow: {
    gap: Spacing.xs,
  },
  meterHead: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: Spacing.sm,
  },
  meterName: {
    flexShrink: 1,
    fontSize: 15,
    color: Colors.text,
  },
  meterFigure: {
    fontSize: 14,
    color: Colors.textMuted,
    fontVariant: ['tabular-nums'],
  },
  track: {
    height: 8,
    borderRadius: 4,
    backgroundColor: METER_TRACK,
    overflow: 'hidden',
  },
  fill: {
    height: 8,
    borderRadius: 4,
    backgroundColor: METER_FILL,
  },
});
