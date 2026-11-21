import { render, screen, userEvent } from '@testing-library/react-native';
import { Linking } from 'react-native';

import { SupportCard } from '@/features/safety/support-card';

const notice = {
  category: 'self_harm',
  message: 'Lütfen hemen güvendiğin bir yetişkinle konuş.',
  resources: [
    { name: 'Acil Çağrı', phone: '112', note: 'Tehlikedeysen.' },
    { name: 'ALO 183 Sosyal Destek Hattı', phone: '183', note: 'Ücretsiz destek.' },
  ],
};

describe('SupportCard', () => {
  it('sabit mesajı ve yardım hatlarını aranabilir bağlantı olarak gösterir', async () => {
    const openURL = jest.spyOn(Linking, 'openURL').mockResolvedValue(undefined);
    const user = userEvent.setup();
    await render(<SupportCard notice={notice} />);

    expect(screen.getByText(notice.message)).toBeOnTheScreen();

    await user.press(screen.getByRole('link', { name: 'Acil Çağrı, 112 numarasını ara' }));
    expect(openURL).toHaveBeenCalledWith('tel:112');
    expect(screen.getByRole('link', { name: /183 numarasını ara/ })).toBeOnTheScreen();
  });
});
