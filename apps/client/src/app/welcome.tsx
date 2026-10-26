import { router } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { Button } from '@/components/button';
import { Screen } from '@/components/screen';
import { Colors, Spacing } from '@/constants/theme';

export default function WelcomeScreen() {
  return (
    <Screen>
      <View style={styles.hero}>
        <Text accessibilityRole="header" style={styles.brand}>
          Hint.ai
        </Text>
        <Text style={styles.tagline}>Cevabı değil, ipucunu veren öğrenme arkadaşı.</Text>
      </View>
      <Button label="Giriş yap" onPress={() => router.push('/login')} />
      <Button
        label="Ebeveyn hesabı oluştur"
        variant="secondary"
        onPress={() => router.push('/register')}
      />
      <Text style={styles.note}>
        Çocuğunun cihazını mı bağlıyorsun? Ebeveyn panelinde oluşturduğun eşleştirme bağlantısını
        bu cihazda aç.
      </Text>
    </Screen>
  );
}

const styles = StyleSheet.create({
  hero: {
    alignItems: 'center',
    gap: Spacing.sm,
    paddingVertical: Spacing.xl,
  },
  brand: {
    fontSize: 40,
    fontWeight: '800',
    color: Colors.guardian,
  },
  tagline: {
    fontSize: 17,
    textAlign: 'center',
    color: Colors.textMuted,
  },
  note: {
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
    color: Colors.textMuted,
  },
});
