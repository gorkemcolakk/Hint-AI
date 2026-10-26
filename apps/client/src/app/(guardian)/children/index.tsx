import { useMutation, useQuery } from '@tanstack/react-query';
import { router } from 'expo-router';
import { ActivityIndicator, Pressable, StyleSheet, Text } from 'react-native';

import { api } from '@/api/client';
import { describeError, unwrap } from '@/api/errors';
import { signOut } from '@/auth/auth';
import { Button } from '@/components/button';
import { ErrorMessage } from '@/components/error-message';
import { Screen } from '@/components/screen';
import { Colors, Radius, Spacing } from '@/constants/theme';

export default function ChildrenScreen() {
  const profiles = useQuery({
    queryKey: ['children'],
    queryFn: () => unwrap(api.GET('/v1/children')),
  });
  const logout = useMutation({ mutationFn: signOut });

  return (
    <Screen hasHeader>
      {profiles.isPending ? <ActivityIndicator color={Colors.guardian} /> : null}
      {profiles.isError ? (
        <>
          <ErrorMessage message={describeError(profiles.error)} />
          <Button label="Tekrar dene" variant="secondary" onPress={() => profiles.refetch()} />
        </>
      ) : null}
      {profiles.data?.length === 0 ? (
        <Text style={styles.empty}>
          Henüz çocuk profili eklemedin. İlk profili ekleyerek başlayabilirsin.
        </Text>
      ) : null}
      {profiles.data?.map((profile) => (
        <Pressable
          key={profile.id}
          accessibilityRole="button"
          accessibilityLabel={`${profile.nickname}, ${profile.grade}. sınıf`}
          onPress={() => router.push({ pathname: '/children/[id]', params: { id: profile.id } })}
          style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}>
          <Text style={styles.cardTitle}>{profile.nickname}</Text>
          <Text style={styles.cardMeta}>
            {profile.grade}. sınıf · {profile.age_band} yaş
          </Text>
        </Pressable>
      ))}
      <Button label="Çocuk ekle" onPress={() => router.push('/children/new')} />
      <Button
        label="Çıkış yap"
        variant="secondary"
        onPress={() => logout.mutate()}
        loading={logout.isPending}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  empty: {
    fontSize: 16,
    lineHeight: 22,
    color: Colors.textMuted,
  },
  card: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: Spacing.md,
    gap: Spacing.xs,
  },
  cardPressed: {
    opacity: 0.85,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.text,
  },
  cardMeta: {
    fontSize: 14,
    color: Colors.textMuted,
  },
});
