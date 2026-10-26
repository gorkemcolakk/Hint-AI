import { useMutation, useQueryClient } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, Text } from 'react-native';

import { api } from '@/api/client';
import { describeError, unwrap } from '@/api/errors';
import { Button } from '@/components/button';
import { Checkbox } from '@/components/checkbox';
import { ErrorMessage } from '@/components/error-message';
import { Screen } from '@/components/screen';
import { TextField } from '@/components/text-field';
import { Colors } from '@/constants/theme';
import {
  CONSENT_OPTIONS,
  type ConsentPurpose,
  type NewChildPayload,
  validateNewChild,
} from '@/features/children/new-child';

export default function NewChildScreen() {
  const queryClient = useQueryClient();
  const [nickname, setNickname] = useState('');
  const [birthYear, setBirthYear] = useState('');
  const [grade, setGrade] = useState('');
  // Rıza kutuları önceden işaretli gelmez (Bölüm 10.5).
  const [purposes, setPurposes] = useState<ConsentPurpose[]>([]);
  const [formError, setFormError] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: (payload: NewChildPayload) => unwrap(api.POST('/v1/children', { body: payload })),
    onSuccess: async (child) => {
      await queryClient.invalidateQueries({ queryKey: ['children'] });
      router.replace({ pathname: '/children/[id]', params: { id: child.id } });
    },
  });

  function togglePurpose(purpose: ConsentPurpose, checked: boolean) {
    setPurposes((current) =>
      checked ? [...current, purpose] : current.filter((item) => item !== purpose),
    );
  }

  function submit() {
    const result = validateNewChild(
      { nickname, birthYear, grade, purposes },
      new Date().getFullYear(),
    );
    if (!result.ok) {
      setFormError(result.error);
      return;
    }
    setFormError(null);
    create.mutate(result.payload);
  }

  return (
    <Screen hasHeader>
      <TextField
        label="Takma ad"
        hint="Gerçek adı yerine takma ad kullanmanı öneririz."
        value={nickname}
        onChangeText={setNickname}
        maxLength={100}
      />
      <TextField
        label="Doğum yılı"
        value={birthYear}
        onChangeText={setBirthYear}
        keyboardType="number-pad"
        maxLength={4}
      />
      <TextField
        label="Sınıf"
        value={grade}
        onChangeText={setGrade}
        keyboardType="number-pad"
        maxLength={2}
      />
      <Text accessibilityRole="header" style={styles.section}>
        Rıza tercihleri
      </Text>
      <Text style={styles.note}>Hizmet rızası zorunludur; diğerleri isteğe bağlıdır.</Text>
      {CONSENT_OPTIONS.map((option) => (
        <Checkbox
          key={option.purpose}
          label={option.label}
          description={option.description}
          checked={purposes.includes(option.purpose)}
          onChange={(checked) => togglePurpose(option.purpose, checked)}
        />
      ))}
      <ErrorMessage message={formError ?? (create.error ? describeError(create.error) : null)} />
      <Button label="Profili oluştur" onPress={submit} loading={create.isPending} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  section: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.text,
  },
  note: {
    fontSize: 14,
    lineHeight: 20,
    color: Colors.textMuted,
  },
});
