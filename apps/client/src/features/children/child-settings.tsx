import { useMutation, useQueryClient } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { api } from '@/api/client';
import { describeError, unwrap } from '@/api/errors';
import { Button } from '@/components/button';
import { CopyButton } from '@/components/copy-button';
import { ErrorMessage } from '@/components/error-message';
import { TextField } from '@/components/text-field';
import { Colors, Radius, Spacing } from '@/constants/theme';
import { CONSENT_OPTIONS, type ConsentPurpose } from '@/features/children/new-child';
import {
  type ChildProfile,
  DAILY_LIMIT_PRESETS,
  exportChildDataBundle,
  PRIVACY_LEVEL_OPTIONS,
  type PrivacyLevel,
  requestDeleteChildProfile,
  SOLUTION_POLICY_OPTIONS,
  type SolutionPolicy,
  validateChildSettings,
} from '@/features/children/settings-logic';

const OPTIONAL_CONSENTS = CONSENT_OPTIONS.filter((item) => item.purpose !== 'service');

export function ChildSettings({ profile }: { profile: ChildProfile }) {
  const queryClient = useQueryClient();
  const [expanded, setExpanded] = useState(false);
  const [nickname, setNickname] = useState(profile.nickname);
  const [dailyLimit, setDailyLimit] = useState(String(profile.daily_new_problem_limit));
  const [privacyLevel, setPrivacyLevel] = useState<PrivacyLevel>(
    profile.privacy_level === 'full_transcript' ? 'full_transcript' : 'summary_only',
  );
  const [solutionPolicy, setSolutionPolicy] = useState<SolutionPolicy>(
    (SOLUTION_POLICY_OPTIONS.find((opt) => opt.value === profile.solution_policy)?.value ??
      'never') as SolutionPolicy,
  );
  const [formError, setFormError] = useState<string | null>(null);
  const [savedNotice, setSavedNotice] = useState<string | null>(null);
  const [consentNotice, setConsentNotice] = useState<string | null>(null);
  const [exportedJson, setExportedJson] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleteConfirmName, setDeleteConfirmName] = useState('');
  const [deleteNotice, setDeleteNotice] = useState<string | null>(null);

  function toggleExpand() {
    if (!expanded) {
      setNickname(profile.nickname);
      setDailyLimit(String(profile.daily_new_problem_limit));
      setPrivacyLevel(
        profile.privacy_level === 'full_transcript' ? 'full_transcript' : 'summary_only',
      );
      setSolutionPolicy(
        (SOLUTION_POLICY_OPTIONS.find((opt) => opt.value === profile.solution_policy)?.value ??
          'never') as SolutionPolicy,
      );
      setFormError(null);
      setSavedNotice(null);
    }
    setExpanded((prev) => !prev);
  }

  const updateSettings = useMutation({
    mutationFn: (payload: {
      nickname: string;
      daily_new_problem_limit: number;
      privacy_level: PrivacyLevel;
      solution_policy: SolutionPolicy;
    }) =>
      unwrap(
        api.PATCH('/v1/children/{child_id}', {
          params: { path: { child_id: profile.id } },
          body: payload,
        }),
      ),
    onSuccess: async () => {
      setSavedNotice('Ayarlar kaydedildi.');
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['children'] }),
        queryClient.invalidateQueries({ queryKey: ['children', profile.id] }),
      ]);
    },
  });

  const updateConsent = useMutation({
    mutationFn: (params: { purpose: ConsentPurpose; grant: boolean; label: string }) =>
      unwrap(
        api.POST('/v1/children/{child_id}/consents', {
          params: { path: { child_id: profile.id } },
          body: { purposes: [params.purpose], grant: params.grant },
        }),
      ),
    onSuccess: (_, variables) => {
      setConsentNotice(
        `${variables.label}: ${variables.grant ? 'izin verildi' : 'izin geri çekildi'}.`,
      );
    },
  });

  const exportData = useMutation({
    mutationFn: () => exportChildDataBundle(profile),
    onSuccess: (json) => setExportedJson(json),
  });

  const deleteChild = useMutation({
    mutationFn: async () => {
      const res = await requestDeleteChildProfile(profile.id);
      if (!res.deleted) {
        await unwrap(
          api.POST('/v1/children/{child_id}/consents', {
            params: { path: { child_id: profile.id } },
            body: {
              purposes: ['llm_processing', 'photo_processing', 'analytics'],
              grant: false,
            },
          }),
        );
      }
      return res;
    },
    onSuccess: async (res) => {
      if (res.deleted) {
        await queryClient.invalidateQueries({ queryKey: ['children'] });
        router.replace('/children');
        return;
      }
      setConfirmDelete(false);
      setDeleteConfirmName('');
      setDeleteNotice(res.reason);
    },
  });

  function save() {
    setSavedNotice(null);
    const checked = validateChildSettings({ nickname, dailyLimit });
    if (!checked.ok) {
      setFormError(checked.error);
      return;
    }
    setFormError(null);
    updateSettings.mutate({
      nickname: checked.nickname,
      daily_new_problem_limit: checked.dailyLimit,
      privacy_level: privacyLevel,
      solution_policy: solutionPolicy,
    });
  }

  return (
    <View style={styles.section}>
      <View style={styles.headerRow}>
        <Text accessibilityRole="header" style={styles.title}>
          Ayarlar, Rıza ve Veri Hakları
        </Text>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={expanded ? 'Ayarları daralt' : 'Ayarları düzenle'}
          onPress={toggleExpand}
          style={styles.toggleBtn}>
          <Text style={styles.toggleText}>{expanded ? 'Gizle' : 'Düzenle'}</Text>
        </Pressable>
      </View>

      {!expanded ? (
        <View style={styles.summaryCard}>
          <Text style={styles.summaryLine}>
            Günlük yeni soru sınırı: <Text style={styles.bold}>{profile.daily_new_problem_limit}</Text>
          </Text>
          <Text style={styles.summaryLine}>
            Gizlilik düzeyi:{' '}
            <Text style={styles.bold}>
              {profile.privacy_level === 'full_transcript'
                ? 'Maskeli soru metinleri açık'
                : 'Yalnızca konu özeti'}
            </Text>
          </Text>
          <Text style={styles.summaryHint}>
            Soru limiti, mahremiyet ayarı, KVKK rızaları ve veri indirme/silme için “Düzenle”ye
            dokun.
          </Text>
        </View>
      ) : (
        <>
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Profil ve Öğrenme Politikası</Text>
            <TextField
              label="Takma ad"
              value={nickname}
              onChangeText={setNickname}
              maxLength={100}
            />

            <TextField
              label="Günlük yeni soru sınırı"
              hint="Başlanmış sorular sınır dolsa da tamamlanabilir (0–100)."
              value={dailyLimit}
              onChangeText={setDailyLimit}
              keyboardType="number-pad"
              maxLength={3}
            />
            <View style={styles.presetRow}>
              {DAILY_LIMIT_PRESETS.map((preset) => {
                const active = dailyLimit.trim() === String(preset);
                return (
                  <Pressable
                    key={preset}
                    accessibilityRole="button"
                    accessibilityLabel={`Günlük sınırı ${preset} yap`}
                    onPress={() => setDailyLimit(String(preset))}
                    style={[styles.presetChip, active && styles.presetChipActive]}>
                    <Text style={[styles.presetText, active && styles.presetTextActive]}>
                      {preset} soru
                    </Text>
                  </Pressable>
                );
              })}
            </View>

            <Text style={styles.subTitle}>Ebeveyn özetinde gizlilik</Text>
            {profile.age_band === '14-17' ? (
              <Text style={styles.youthNote}>
                14–17 yaş gençlerde güven ve özerklik için varsayılan olarak yalnızca konu özeti
                önerilir; tam soru metni açıldığında gence bilgi verilmelidir.
              </Text>
            ) : null}
            {PRIVACY_LEVEL_OPTIONS.map((option) => {
              const selected = privacyLevel === option.value;
              return (
                <Pressable
                  key={option.value}
                  accessibilityRole="radio"
                  accessibilityLabel={option.label}
                  accessibilityState={{ selected }}
                  onPress={() => setPrivacyLevel(option.value)}
                  style={[styles.choiceRow, selected && styles.choiceSelected]}>
                  <Text style={styles.choiceLabel}>
                    {selected ? '● ' : '○ '}
                    {option.label}
                  </Text>
                  <Text style={styles.choiceDesc}>{option.description}</Text>
                </Pressable>
              );
            })}

            <Text style={styles.subTitle}>Çözüm gösterme politikası</Text>
            {SOLUTION_POLICY_OPTIONS.map((option) => {
              const selected = solutionPolicy === option.value;
              return (
                <Pressable
                  key={option.value}
                  accessibilityRole="radio"
                  accessibilityLabel={option.label}
                  accessibilityState={{ selected }}
                  onPress={() => setSolutionPolicy(option.value)}
                  style={[styles.choiceRow, selected && styles.choiceSelected]}>
                  <Text style={styles.choiceLabel}>
                    {selected ? '● ' : '○ '}
                    {option.label}
                  </Text>
                  <Text style={styles.choiceDesc}>{option.description}</Text>
                </Pressable>
              );
            })}

            <ErrorMessage
              message={
                formError ?? (updateSettings.error ? describeError(updateSettings.error) : null)
              }
            />
            {savedNotice ? (
              <Text role="status" style={styles.successText}>
                ✓ {savedNotice}
              </Text>
            ) : null}
            <Button
              label="Ayarları kaydet"
              loading={updateSettings.isPending}
              onPress={save}
            />
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>KVKK Açık Rıza Yönetimi</Text>
            <Text style={styles.choiceDesc}>
              İsteğe bağlı izinleri dilediğin an verebilir veya geri çekebilirsin. Yapay zekâ izni
              geri çekildiğinde yeni soru ve ipucu üretimi durur.
            </Text>
            {OPTIONAL_CONSENTS.map((item) => (
              <View key={item.purpose} style={styles.consentRow}>
                <View style={styles.consentInfo}>
                  <Text style={styles.choiceLabel}>{item.label}</Text>
                  <Text style={styles.choiceDesc}>{item.description}</Text>
                </View>
                <View style={styles.consentActions}>
                  <Pressable
                    accessibilityRole="button"
                    accessibilityLabel={`${item.label} izni ver`}
                    disabled={updateConsent.isPending}
                    onPress={() =>
                      updateConsent.mutate({
                        purpose: item.purpose,
                        grant: true,
                        label: item.label,
                      })
                    }
                    style={[styles.consentBtn, styles.consentGrant]}>
                    <Text style={styles.consentGrantText}>İzin ver</Text>
                  </Pressable>
                  <Pressable
                    accessibilityRole="button"
                    accessibilityLabel={`${item.label} iznini geri çek`}
                    disabled={updateConsent.isPending}
                    onPress={() =>
                      updateConsent.mutate({
                        purpose: item.purpose,
                        grant: false,
                        label: item.label,
                      })
                    }
                    style={styles.consentBtn}>
                    <Text style={styles.consentRevokeText}>Geri çek</Text>
                  </Pressable>
                </View>
              </View>
            ))}
            <ErrorMessage
              message={updateConsent.error ? describeError(updateConsent.error) : null}
            />
            {consentNotice ? (
              <Text role="status" style={styles.successText}>
                ✓ {consentNotice}
              </Text>
            ) : null}
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Veri Taşıma ve Silme (KVKK)</Text>
            <Text style={styles.choiceDesc}>
              Çocuğuna ait profil ve ilerleme verilerini JSON olarak indirebilir ya da profilin
              silinmesini talep edebilirsin.
            </Text>
            <Button
              label="Çocuk verilerini indir (JSON)"
              variant="secondary"
              loading={exportData.isPending}
              onPress={() => exportData.mutate()}
            />
            <ErrorMessage message={exportData.error ? describeError(exportData.error) : null} />
            {exportedJson ? (
              <View style={styles.exportPreview}>
                <Text style={styles.successText}>
                  ✓ Veri paketi hazırlandı ({exportedJson.length} karakter).
                </Text>
                <CopyButton
                  value={exportedJson}
                  label="JSON verisini kopyala"
                  color={Colors.guardian}
                />
              </View>
            ) : null}

            {confirmDelete ? (
              <View style={styles.deleteBox}>
                <Text style={styles.deleteWarning}>
                  Bu işlem geri alınamaz. Onaylamak için çocuğun takma adını ({profile.nickname})
                  aşağıya yaz:
                </Text>
                <TextField
                  label="Takma adı doğrula"
                  value={deleteConfirmName}
                  onChangeText={setDeleteConfirmName}
                  autoCapitalize="none"
                />
                <ErrorMessage
                  message={deleteChild.error ? describeError(deleteChild.error) : null}
                />
                <Button
                  label="Kalıcı olarak sil"
                  color={Colors.danger}
                  loading={deleteChild.isPending}
                  disabled={deleteConfirmName.trim() !== profile.nickname}
                  onPress={() => deleteChild.mutate()}
                />
                <Button
                  label="Vazgeç"
                  variant="secondary"
                  onPress={() => {
                    setConfirmDelete(false);
                    setDeleteConfirmName('');
                  }}
                />
              </View>
            ) : (
              <Button
                label="Çocuk profilini ve verileri sil"
                variant="secondary"
                color={Colors.danger}
                onPress={() => setConfirmDelete(true)}
              />
            )}
            {deleteNotice ? (
              <Text role="status" style={styles.youthNote}>
                {deleteNotice}
              </Text>
            ) : null}
          </View>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  section: { gap: Spacing.md },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: Spacing.sm,
  },
  title: { fontSize: 20, fontWeight: '700', color: Colors.text, flex: 1 },
  toggleBtn: {
    minHeight: 36,
    paddingHorizontal: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.guardian,
    justifyContent: 'center',
    backgroundColor: Colors.surface,
  },
  toggleText: { fontSize: 14, fontWeight: '600', color: Colors.guardian },
  summaryCard: {
    gap: 4,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
  },
  summaryLine: { fontSize: 14, color: Colors.text },
  bold: { fontWeight: '700' },
  summaryHint: { fontSize: 13, color: Colors.textMuted, marginTop: 4 },
  card: {
    gap: Spacing.md,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
  },
  cardTitle: { fontSize: 17, fontWeight: '700', color: Colors.text },
  subTitle: { fontSize: 15, fontWeight: '700', color: Colors.text },
  presetRow: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.xs },
  presetChip: {
    minHeight: 36,
    paddingHorizontal: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.background,
    justifyContent: 'center',
  },
  presetChipActive: {
    borderColor: Colors.guardian,
    backgroundColor: '#EBF1F8',
  },
  presetText: { fontSize: 13, fontWeight: '600', color: Colors.text },
  presetTextActive: { color: Colors.guardian },
  choiceRow: {
    gap: 2,
    padding: Spacing.sm,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  choiceSelected: {
    borderColor: Colors.guardian,
    backgroundColor: '#F2F6FC',
  },
  choiceLabel: { fontSize: 14, fontWeight: '700', color: Colors.text },
  choiceDesc: { fontSize: 13, lineHeight: 19, color: Colors.textMuted },
  youthNote: {
    fontSize: 13,
    lineHeight: 19,
    color: '#7A4A0B',
    backgroundColor: '#FFF8E6',
    padding: Spacing.sm,
    borderRadius: Radius.md,
  },
  consentRow: {
    gap: Spacing.sm,
    paddingBottom: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  consentInfo: { gap: 2 },
  consentActions: { flexDirection: 'row', gap: Spacing.xs },
  consentBtn: {
    minHeight: 36,
    paddingHorizontal: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    justifyContent: 'center',
  },
  consentGrant: { borderColor: Colors.guardian, backgroundColor: '#F2F6FC' },
  consentGrantText: { fontSize: 13, fontWeight: '600', color: Colors.guardian },
  consentRevokeText: { fontSize: 13, fontWeight: '600', color: Colors.danger },
  successText: { fontSize: 14, fontWeight: '600', color: Colors.child },
  exportPreview: { gap: Spacing.xs },
  deleteBox: {
    gap: Spacing.sm,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1.5,
    borderColor: Colors.danger,
    backgroundColor: '#FDF2F1',
  },
  deleteWarning: { fontSize: 14, lineHeight: 20, color: Colors.danger, fontWeight: '600' },
});
