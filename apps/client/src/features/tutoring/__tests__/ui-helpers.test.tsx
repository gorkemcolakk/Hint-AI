import { render, screen, userEvent } from '@testing-library/react-native';

import { ApiError } from '@/api/errors';
import { HintCard } from '@/features/tutoring/hint-card';
import { themeForAgeBand } from '@/features/tutoring/ladder';
import { isQuotaError, QuotaChecklistCard } from '@/features/tutoring/quota-checklist';
import {
  dismissBreakReminder,
  rememberRecentProblem,
  resetChildUiState,
  shouldSuggestBreak,
  STUDY_BREAK_REMINDER_MS,
} from '@/features/tutoring/reading-preferences';
import { parseSseEvents } from '@/features/tutoring/stream-hint';

describe('SSE ayrıştırıcı (parseSseEvents)', () => {
  it('parçalı token olaylarını birleştirir ve Bölüm 9.2 hint olayını çözer', () => {
    const partials: string[] = [];
    const sse = [
      'event: delta\ndata: {"text":"Önce iki "}\n\n',
      'event: delta\ndata: {"text":"tarafı düşün."}\n\n',
      'event: hint\ndata: {"hint_id":"h-1","level":1,"text":"Önce iki tarafı düşün.","can_request_next":true}\n\n',
    ].join('');

    const final = parseSseEvents(sse, (text) => partials.push(text));
    expect(partials).toEqual(['Önce iki ', 'Önce iki tarafı düşün.']);
    expect(final?.hint?.id).toBe('h-1');
    expect(final?.hint?.level).toBe(1);
    expect(final?.can_request_next).toBe(true);
  });
});

describe('okuma ve mola yardımcıları', () => {
  afterEach(() => {
    resetChildUiState();
  });

  it('30 dakika sonunda mola önerir, kapatılınca tekrar göstermez', () => {
    const start = Date.now();
    expect(shouldSuggestBreak(start + 5_000)).toBe(false);
    expect(shouldSuggestBreak(start + STUDY_BREAK_REMINDER_MS + 1_000)).toBe(true);
    dismissBreakReminder();
    expect(shouldSuggestBreak(start + STUDY_BREAK_REMINDER_MS + 60_000)).toBe(false);
  });

  it('son soruyu kaydeder ve oturum sıfırlanınca temizler', () => {
    rememberRecentProblem({
      id: 'prob-1',
      preview: '3x + 5 = 20',
      topic: 'Denklemler',
      solved: false,
    });
    resetChildUiState();
    expect(shouldSuggestBreak(Date.now())).toBe(false);
  });
});

describe('QuotaChecklistCard ve HintCard etkileşimleri', () => {
  const theme = themeForAgeBand('11-13');

  it('429 hatasını kota hatası olarak tanır ve kontrol listesi maddelerini işaretler', async () => {
    expect(isQuotaError(new ApiError('Limit doldu', 429))).toBe(true);
    expect(isQuotaError(new ApiError('Yetkisiz', 401))).toBe(false);

    const user = userEvent.setup();
    await render(<QuotaChecklistCard theme={theme} />);
    const firstItem = screen.getByRole('checkbox', {
      name: /Soruda hangi sayılar verilmiş/i,
    });
    expect(firstItem).not.toBeChecked();
    await user.press(firstItem);
    expect(firstItem).toBeChecked();
  });

  it('son ipucunda "Tam anlamadım" seçilince açıklama isteğini tetikler', async () => {
    const onClarify = jest.fn();
    const user = userEvent.setup();
    await render(
      <HintCard
        id="hint-42"
        level={0}
        levelName="Anlama kontrolü"
        text="Bu soruda neyi arıyoruz?"
        latest
        theme={theme}
        canRequestClarification
        onRequestClarification={onClarify}
      />,
    );

    const unclearBtn = screen.getByRole('button', { name: 'Bu ipucunu tam anlamadım' });
    await user.press(unclearBtn);
    expect(onClarify).toHaveBeenCalledTimes(1);
  });
});
