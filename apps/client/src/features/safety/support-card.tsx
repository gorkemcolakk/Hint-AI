import { Linking, Pressable, StyleSheet, Text, View } from 'react-native';

import type { components } from '@/api/schema';
import { Colors, Radius, Spacing } from '@/constants/theme';

export type SafetyNotice = components['schemas']['SafetyNotice'];

type Props = { notice: SafetyNotice };

/**
 * Güvenlik kapısı akışı durdurduğunda gösterilen sakin destek kartı. Metin sunucudaki sabit,
 * önceden yazılmış şablondan gelir; model üretmez.
 */
export function SupportCard({ notice }: Props) {
  return (
    <View role="alert" accessibilityLiveRegion="assertive" style={styles.card}>
      <Text style={styles.message}>{notice.message}</Text>
      {notice.resources.map((resource) => (
        <Pressable
          key={resource.phone}
          accessibilityRole="link"
          accessibilityLabel={`${resource.name}, ${resource.phone} numarasını ara`}
          onPress={() => void Linking.openURL(`tel:${resource.phone}`)}
          style={({ pressed }) => [styles.resource, pressed && styles.pressed]}>
          <Text style={styles.phone}>{resource.phone}</Text>
          <View style={styles.resourceText}>
            <Text style={styles.resourceName}>{resource.name}</Text>
            <Text style={styles.resourceNote}>{resource.note}</Text>
          </View>
        </Pressable>
      ))}
    </View>
  );
}

/** Akış sürerken gösterilen nazik not (ör. cevap isteme, kişisel bilgi paylaşma). */
export function NoticeText({ text }: { text: string }) {
  return (
    <Text role="status" accessibilityLiveRegion="polite" style={styles.notice}>
      {text}
    </Text>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: Spacing.md,
    padding: Spacing.md,
    borderRadius: Radius.md,
    backgroundColor: '#FFF8E6',
    borderWidth: 2,
    borderColor: '#B7791F',
  },
  message: {
    fontSize: 17,
    lineHeight: 25,
    color: Colors.text,
  },
  resource: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
    minHeight: 52,
    padding: Spacing.sm,
    borderRadius: Radius.md,
    backgroundColor: Colors.surface,
  },
  pressed: {
    opacity: 0.8,
  },
  phone: {
    fontSize: 24,
    fontWeight: '800',
    color: '#7A4A0B',
    minWidth: 56,
    textAlign: 'center',
  },
  resourceText: {
    flex: 1,
    gap: 2,
  },
  resourceName: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.text,
  },
  resourceNote: {
    fontSize: 13,
    color: Colors.textMuted,
  },
  notice: {
    fontSize: 15,
    lineHeight: 21,
    color: Colors.textMuted,
    fontStyle: 'italic',
  },
});
