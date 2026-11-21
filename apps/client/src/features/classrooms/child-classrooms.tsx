import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import { describeError, unwrap } from '@/api/errors';
import { Button } from '@/components/button';
import { ErrorMessage } from '@/components/error-message';
import { TextField } from '@/components/text-field';
import { Colors, Radius, Spacing } from '@/constants/theme';

/**
 * Ebeveynin çocuğunu bir öğretmen sınıfına kaydetmesi. Katılmak açık onaydır; önce öğretmenin
 * neleri göreceği gösterilir. Sınıftan çıkarmak onayı geri çeker.
 */
export function ChildClassrooms({ childId }: { childId: string }) {
  const queryClient = useQueryClient();
  const [code, setCode] = useState('');
  const [leaving, setLeaving] = useState<string | null>(null);
  const queryKey = ['children', childId, 'classrooms'];

  const list = useQuery({
    queryKey,
    queryFn: () =>
      unwrap(
        api.GET('/v1/children/{child_id}/classrooms', { params: { path: { child_id: childId } } }),
      ),
  });
  const preview = useMutation({
    mutationFn: (value: string) =>
      unwrap(api.POST('/v1/classrooms/preview', { body: { code: value } })),
  });
  const join = useMutation({
    mutationFn: (value: string) =>
      unwrap(
        api.POST('/v1/children/{child_id}/classrooms', {
          params: { path: { child_id: childId } },
          body: { code: value },
        }),
      ),
    onSuccess: () => {
      setCode('');
      preview.reset();
      return queryClient.invalidateQueries({ queryKey });
    },
  });
  const leave = useMutation({
    mutationFn: (classroomId: string) =>
      unwrap(
        api.DELETE('/v1/children/{child_id}/classrooms/{classroom_id}', {
          params: { path: { child_id: childId, classroom_id: classroomId } },
        }),
      ),
    onSuccess: () => {
      setLeaving(null);
      return queryClient.invalidateQueries({ queryKey });
    },
  });
  const error = list.error ?? preview.error ?? join.error ?? leave.error;

  return (
    <View style={styles.section}>
      <Text accessibilityRole="header" style={styles.title}>
        Sınıflar
      </Text>

      {list.data?.map((classroom) => (
        <View key={classroom.id} style={styles.card}>
          <Text style={styles.name}>{classroom.name}</Text>
          <Text style={styles.meta}>{classroom.teacher_name}</Text>
          {leaving === classroom.id ? (
            <>
              <Text style={styles.warning}>
                Öğretmen bu çocuğun özetini artık göremeyecek. Emin misin?
              </Text>
              <Button
                label="Evet, sınıftan çıkar"
                color={Colors.danger}
                loading={leave.isPending}
                onPress={() => leave.mutate(classroom.id)}
              />
              <Button label="Vazgeç" variant="secondary" onPress={() => setLeaving(null)} />
            </>
          ) : (
            <Button
              label="Sınıftan çıkar"
              variant="secondary"
              onPress={() => setLeaving(classroom.id)}
            />
          )}
        </View>
      ))}
      {list.data?.length === 0 ? (
        <Text style={styles.meta}>Çocuğun henüz bir sınıfa kayıtlı değil.</Text>
      ) : null}

      {preview.data ? (
        <View style={[styles.card, styles.previewCard]}>
          <Text style={styles.name}>{preview.data.name}</Text>
          <Text style={styles.meta}>
            {preview.data.teacher_name}
            {preview.data.grade ? ` · ${preview.data.grade}. sınıf` : ''}
          </Text>
          <Text style={styles.body}>{preview.data.teacher_sees}</Text>
          <Button
            label="Onayla ve katıl"
            color={Colors.teacher}
            loading={join.isPending}
            onPress={() => join.mutate(code)}
          />
          <Button label="Vazgeç" variant="secondary" onPress={() => preview.reset()} />
        </View>
      ) : (
        <View style={styles.joinRow}>
          <TextField
            label="Öğretmenden aldığın davet kodu"
            hint="Örnek: DEMO6A"
            value={code}
            onChangeText={setCode}
            autoCapitalize="characters"
            autoCorrect={false}
            maxLength={20}
          />
          <Button
            label="Sınıfı bul"
            variant="secondary"
            loading={preview.isPending}
            disabled={code.trim().length < 4}
            onPress={() => preview.mutate(code)}
          />
        </View>
      )}
      <ErrorMessage message={error ? describeError(error) : null} />
    </View>
  );
}

const styles = StyleSheet.create({
  section: { gap: Spacing.md },
  title: { fontSize: 20, fontWeight: '700', color: Colors.text },
  card: {
    gap: Spacing.sm,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
  },
  previewCard: { borderColor: Colors.teacher, borderWidth: 2 },
  name: { fontSize: 17, fontWeight: '700', color: Colors.text },
  meta: { fontSize: 14, color: Colors.textMuted },
  body: { fontSize: 14, lineHeight: 20, color: Colors.text },
  warning: { fontSize: 14, lineHeight: 20, color: Colors.danger },
  joinRow: { gap: Spacing.sm },
});
