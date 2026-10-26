import { render, screen, userEvent } from '@testing-library/react-native';

import { Checkbox } from '@/components/checkbox';

describe('Checkbox', () => {
  it('erişilebilir adı ve işaret durumunu ekran okuyucuya bildirir', async () => {
    const onChange = jest.fn();
    const user = userEvent.setup();
    await render(<Checkbox label="Hizmet (zorunlu)" checked={false} onChange={onChange} />);

    const box = screen.getByRole('checkbox', { name: 'Hizmet (zorunlu)' });
    expect(box).not.toBeChecked();

    await user.press(box);
    expect(onChange).toHaveBeenCalledWith(true);
  });

  it('işaretliyken dokununca işareti kaldırır', async () => {
    const onChange = jest.fn();
    const user = userEvent.setup();
    await render(<Checkbox label="Analitik" checked onChange={onChange} />);

    const box = screen.getByRole('checkbox', { name: 'Analitik' });
    expect(box).toBeChecked();

    await user.press(box);
    expect(onChange).toHaveBeenCalledWith(false);
  });
});
