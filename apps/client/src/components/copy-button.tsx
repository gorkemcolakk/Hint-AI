import { useEffect, useRef, useState } from 'react';
import { Platform, Pressable, Share, StyleSheet, Text } from 'react-native';

import { Colors, Radius, Spacing } from '@/constants/theme';

type Props = {
  value: string;
  label?: string;
  copiedLabel?: string;
  shareMessage?: string;
  color?: string;
};

async function writeClipboardWeb(value: string): Promise<boolean> {
  if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(value);
      return true;
    } catch {
      // Güvenli olmayan bağlamda yedek kopyalama yoluna düş.
    }
  }
  if (typeof document !== 'undefined') {
    const area = document.createElement('textarea');
    area.value = value;
    area.setAttribute('readonly', 'true');
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(area);
    return ok;
  }
  return false;
}

/**
 * Web'de panoya kopyalar ve kısa süreli onay gösterir; mobilde sistem paylaşım
 * penceresini açar (üçüncü taraf yerel modül gerektirmez).
 */
export function CopyButton({
  value,
  label = Platform.OS === 'web' ? 'Kopyala' : 'Paylaş',
  copiedLabel = '✓ Kopyalandı',
  shareMessage,
  color = Colors.guardian,
}: Props) {
  const [copied, setCopied] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  async function handlePress() {
    if (Platform.OS === 'web') {
      const ok = await writeClipboardWeb(value);
      if (ok) {
        setCopied(true);
        if (timerRef.current) clearTimeout(timerRef.current);
        timerRef.current = setTimeout(() => setCopied(false), 2200);
      }
      return;
    }
    await Share.share({ message: shareMessage ?? value });
  }

  const displayLabel = copied ? copiedLabel : label;

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={displayLabel}
      accessibilityLiveRegion="polite"
      onPress={() => void handlePress()}
      style={({ pressed }) => [
        styles.button,
        { borderColor: color },
        copied && { backgroundColor: color },
        pressed && styles.pressed,
      ]}>
      <Text style={[styles.label, { color: copied ? Colors.onPrimary : color }]}>
        {displayLabel}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 44,
    paddingHorizontal: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  label: {
    fontSize: 15,
    fontWeight: '600',
  },
  pressed: {
    opacity: 0.85,
  },
});
