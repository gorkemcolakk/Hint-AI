import { StyleSheet, Text, type StyleProp, type TextStyle } from 'react-native';

const SUPERSCRIPTS: Record<string, string> = {
  '0': '⁰',
  '1': '¹',
  '2': '²',
  '3': '³',
  '4': '⁴',
  '5': '⁵',
  '6': '⁶',
  '7': '⁷',
  '8': '⁸',
  '9': '⁹',
  '+': '⁺',
  '-': '⁻',
  n: 'ⁿ',
};

function toSuperscript(exp: string): string | null {
  let out = '';
  for (const ch of exp) {
    const mapped = SUPERSCRIPTS[ch];
    if (!mapped) return null;
    out += mapped;
  }
  return out;
}

function wrapFractionPart(part: string): string {
  const trimmed = part.trim();
  return /^[a-zA-Z0-9ğüşöçıİĞÜŞÖÇ]+$/.test(trimmed) ? trimmed : `(${trimmed})`;
}

/**
 * Ham LaTeX / matematik dizgilerini hem web hem mobilde okunaklı matematik gösterimine
 * çevirir (ör. `\frac{3}{4}` -> `3/4`, `x^2` -> `x²`, `\sqrt{16}` -> `√16`).
 */
export function formatMathDisplay(raw: string): string {
  let text = raw;
  // Satır içi ve blok LaTeX sınırlayıcılarını temizle
  text = text.replace(/\$\$([\s\S]*?)\$\$/g, '$1');
  text = text.replace(/\$([^$\n]+)\$/g, '$1');
  text = text.replace(/\\\(([\s\S]*?)\\\)/g, '$1');
  text = text.replace(/\\\[([\s\S]*?)\\\]/g, '$1');

  // Kesirler: \frac{pay}{payda}
  text = text.replace(/\\d?frac\{([^{}]+)\}\{([^{}]+)\}/g, (_, num: string, den: string) => {
    return `${wrapFractionPart(num)}/${wrapFractionPart(den)}`;
  });

  // Karekök: \sqrt{ifade}
  text = text.replace(/\\sqrt\{([^{}]+)\}/g, (_, inner: string) => {
    const clean = inner.trim();
    return /^[a-zA-Z0-9]+$/.test(clean) ? `√${clean}` : `√(${clean})`;
  });

  // Yaygın matematik sembolleri
  text = text
    .replace(/\\cdot/g, '·')
    .replace(/\\times/g, '×')
    .replace(/\\div/g, '÷')
    .replace(/\\leq?/g, '≤')
    .replace(/\\geq?/g, '≥')
    .replace(/\\neq?/g, '≠')
    .replace(/\\pm/g, '±')
    .replace(/\\pi\b/g, 'π')
    .replace(/\^\\circ|\\degree/g, '°');

  // Üslü ifadeler: x^{12} veya x^2
  text = text.replace(/\^\{([0-9+\-n]+)\}/g, (full, exp: string) => toSuperscript(exp) ?? full);
  text = text.replace(/\^(-?[0-9]+|n)\b/g, (full, exp: string) => toSuperscript(exp) ?? full);

  return text;
}

type Props = {
  children: string;
  comfortableReading?: boolean;
  style?: StyleProp<TextStyle>;
};

export function MathText({ children, comfortableReading = false, style }: Props) {
  const formatted = formatMathDisplay(children);
  return (
    <Text style={[style, comfortableReading && styles.comfortable]}>{formatted}</Text>
  );
}

const styles = StyleSheet.create({
  comfortable: {
    letterSpacing: 0.6,
    lineHeight: 30,
  },
});
