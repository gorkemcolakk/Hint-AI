import { render, screen } from '@testing-library/react-native';

import { formatMathDisplay, MathText } from '@/components/math-text';

describe('MathText ve formatMathDisplay', () => {
  it('LaTeX kesir, kök, üs ve sembolleri okunaklı matematik metnine çevirir', () => {
    expect(formatMathDisplay('$\\frac{3}{4} + \\frac{x+1}{2} = 5$')).toBe('3/4 + (x+1)/2 = 5');
    expect(formatMathDisplay('$$x^2 + y^{10} - 2^{-3}$$')).toBe('x² + y¹⁰ - 2⁻³');
    expect(formatMathDisplay('\\(\\sqrt{16} \\cdot \\sqrt{x+9} \\leq 12\\)')).toBe(
      '√16 · √(x+9) ≤ 12',
    );
    expect(formatMathDisplay('Açı 60^\\circ ve a \\neq b')).toBe('Açı 60° ve a ≠ b');
  });

  it('rahat okuma modunda biçimlendirilmiş metni ekranda gösterir', async () => {
    await render(<MathText comfortableReading>{'Denklem: $3x^2 = 12$'}</MathText>);
    expect(screen.getByText('Denklem: 3x² = 12')).toBeTruthy();
  });
});
