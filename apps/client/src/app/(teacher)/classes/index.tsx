import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import { describeError, unwrap } from '@/api/errors';
import { signOut } from '@/auth/auth';
import { Button } from '@/components/button';
import { ErrorMessage } from '@/components/error-message';
import { Screen } from '@/components/screen';
import { TextField } from '@/components/text-field';
import { Colors, Radius, Spacing } from '@/constants/theme';
import { formatJoinCode } from '@/features/classrooms/heat';

export default function ClassesScreen() {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [grade, setGrade] = useState('');

  const classes = useQuery({
    queryKey: ['classrooms'],
    queryFn: () => unwrap(api.GET('/v1/classrooms')),
  });
  const create = useMutation({
    mutationFn: () =>
      unwrap(
        api.POST('/v1/classrooms', {
          body: { name: name.trim(), grade: grade ? Number(grade) : null },
        }),
      ),
    onSuccess: (classroom) => {
      setName('');
      setGrade('');
      void queryClient.invalidateQueries({ queryKey: ['classrooms'] });
      router.push({ pathname: '/classes/[id]', params: { id: classroom.id } });
    },
  });
  const gradeValid = grade === '' || (/^\d{1,2}$/.test(grade) && +grade >= 1 && +grade <= 12);

  return (
    <Screen hasHeader>
      <Text style={styles.intro}>
        Sınıf oluştur, davet kodunu velilerle paylaş. Veliler onay verdikçe öğrenciler sınıfına
        eklenir; hangi konularda zorlandıklarını özet olarak görürsün.
      </Text>

      {classes.isPending ? <ActivityIndicator color={Colors.teacher} /> : null}
      <ErrorMessage message={classes.isError ? describeError(classes.error) : null} />
      {classes.data?.map((classroom) => (
        <Pressable
          key={classroom.id}
          accessibilityRole="button"
          accessibilityLabel={`${classroom.name}, ${classroom.student_count} öğrenci`}
          onPress={() => router.push({ pathname: '/classes/[id]', params: { id: classroom.id } })}
          style={({ pressed }) => [styles.card, pressed && styles.pressed]}>
          <Text style={styles.name}>{classroom.name}</Text>
          <Text style={styles.meta}>
            {classroom.grade ? `${classroom.grade}. sınıf · ` : ''}
            {classroom.student_count} öğrenci · kod {formatJoinCode(classroom.join_code)}
          </Text>
        </Pressable>
      ))}
      {classes.data?.length === 0 ? <Text style={styles.meta}>Henüz sınıfın yok.</Text> : null}

      <View style={styles.form}>
        <Text accessibilityRole="header" style={styles.formTitle}>
          Yeni sınıf
        </Text>
        <TextField
          label="Sınıf adı"
          hint="Örnek: 6-A Matematik"
          value={name}
          onChangeText={setName}
          maxLength={100}
        />
        <TextField
          label="Sınıf düzeyi (isteğe bağlı)"
          hint="1–12 arası"
          value={grade}
          onChangeText={setGrade}
          keyboardType="number-pad"
          maxLength={2}
        />
        <ErrorMessage
          message={
            !gradeValid
              ? 'Sınıf düzeyi 1 ile 12 arasında olmalı.'
              : create.isError
                ? describeError(create.error)
                : null
          }
        />
        <Button
          label="Sınıf oluştur"
          color={Colors.teacher}
          loading={create.isPending}
          disabled={!name.trim() || !gradeValid}
          onPress={() => create.mutate()}
        />
      </View>

      <Button
        label="Çıkış yap"
        variant="secondary"
        color={Colors.teacher}
        onPress={() => void signOut()}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  intro: { fontSize: 15, lineHeight: 21, color: Colors.textMuted },
  card: {
    gap: Spacing.xs,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    borderLeftWidth: 4,
    borderLeftColor: Colors.teacher,
    backgroundColor: Colors.surface,
  },
  pressed: { opacity: 0.85 },
  name: { fontSize: 18, fontWeight: '700', color: Colors.text },
  meta: { fontSize: 14, color: Colors.textMuted },
  form: {
    gap: Spacing.md,
    padding: Spacing.md,
    borderRadius: Radius.md,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  formTitle: { fontSize: 18, fontWeight: '700', color: Colors.text },
});
