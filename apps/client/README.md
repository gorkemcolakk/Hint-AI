# Hint.ai istemcisi

Expo (React Native + react-native-web) ile tek kod tabanından iOS, Android ve Web. Ebeveyn paneli ve çocuk modu aynı uygulamada, ayrı route grupları olarak yaşar.

## Çalıştırma

Önce API'yi kökten başlat (`docker compose up -d --build`), sonra:

```powershell
npm install
npm run web    # tarayıcıda http://localhost:8081
npm start      # telefonda Expo Go ile açmak için QR kodu
```

**Telefonda (Expo Go):** Telefon ile bilgisayar aynı Wi-Fi ağında olmalı. Uygulama API'ye Metro'yu çalıştıran bilgisayarın adresiyle (`http://<bilgisayar-ip>:8000`) bağlanır; Windows güvenlik duvarı 8000 portunu engelliyorsa izin vermek gerekir.

**API adresini değiştirmek:** `$env:EXPO_PUBLIC_API_URL = "http://192.168.1.20:8000"; npm start`

**CORS:** Web istemcisi yalnızca API'nin `HINT_CORS_ORIGINS` listesindeki adreslerden çağrı yapabilir (varsayılan `http://localhost:8081`).

## Komutlar

| Komut | Açıklama |
|---|---|
| `npm run web` / `npm start` | Geliştirme sunucusu |
| `npm run lint` | ESLint (`eslint-config-expo`) |
| `npm run typecheck` | TypeScript (`strict`) |
| `npm test` | Jest + React Native Testing Library |
| `npm run gen:api` | `openapi.json`'dan `src/api/schema.d.ts` üretir |

API şeması değişince kökten `make client-gen` çalıştır: önce backend'den `openapi.json` dışa aktarılır, sonra tipler üretilir. CI, ikisinin de güncel olduğunu kontrol eder.

## Yapı

```
src/
├─ app/                  # Ekranlar (Expo Router: her dosya bir route)
│  ├─ _layout.tsx        # Sağlayıcılar + oturuma göre erişim kuralları (Stack.Protected)
│  ├─ welcome / login / register / pair
│  ├─ (guardian)/        # Ebeveyn paneli: çocuk listesi, ekleme, eşleştirme
│  └─ (child)/           # Çocuk modu
├─ api/                  # openapi-fetch istemcileri, hata çevirisi, üretilen tipler
├─ auth/                 # Oturum deposu, token saklama, giriş/yenileme/eşleştirme
├─ components/           # Ortak, erişilebilir arayüz bileşenleri
├─ features/             # Ekranlardan bağımsız iş kuralları (ör. çocuk formu doğrulaması)
└─ constants/theme.ts    # Renkler ve boşluklar
```

## Oturum ve güvenlik

- **Ebeveyn:** Access token (15 dk) bitmeden önce refresh token ile yenilenir. Aynı anda gelen istekler tek yenileme çağrısını paylaşır, çünkü refresh token rotasyonlu.
- **Çocuk:** Eşleştirme bağlantısıyla gelen 30 dakikalık token kullanılır. Süre dolunca ebeveynden yeni bağlantı istenir; uzun ömürlü cihaz oturumu M6'da gelecek.
- **Saklama:** Mobilde `expo-secure-store` (Keychain/Keystore). Web'de token'lar yalnızca bellekte tutulur; sayfa yenilenince oturum kapanır.
- **Çocuk moduna geçiş:** Cihaz çocuk moduna geçince ebeveynin refresh token'ı sunucuda iptal edilir.

## Flutter bilenler için kavram haritası

| Flutter | Bu projede |
|---|---|
| `Widget` | Bileşen (fonksiyon): `src/components/button.tsx` |
| `build()` | Bileşenin döndürdüğü JSX |
| `StatefulWidget` + `setState` | `useState` (ör. `src/app/(guardian)/children/new.tsx`) |
| `initState` / `dispose` | `useEffect` (ör. `src/app/_layout.tsx`) |
| `ChangeNotifier` + dinleyiciler | `src/auth/session-store.ts` (`useSyncExternalStore`) |
| `FutureBuilder` | TanStack Query `useQuery` (önbellek ve yeniden deneme dahil) |
| `go_router` + `redirect` | Expo Router: dosya tabanlı route'lar + `Stack.Protected` |
| `Semantics` | `accessibilityRole`, `accessibilityLabel`, `aria-checked` |
| `pubspec.yaml` / pub.dev | `package.json` / npm (`npx expo install` SDK uyumlu sürüm seçer) |
