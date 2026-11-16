# Varsayımlar

> hint-ai-master-plan.md Bölüm 20'de olmayan belirsiz kararlarda yapılan varsayımlar burada tutulur.

- M0'da `GET /healthz` (canlılık) her zaman 200 döner; `GET /readyz` (hazırlık) DB + Redis erişimini kontrol eder, hazır değilse 503 döner.
- M0 kapsamı yalnızca altyapıdır; kimlik, veri modeli ve moderasyon M1'den itibaren eklenir.
- Yerel makinede Docker yoksa `docker compose up` yerine API `uvicorn` ile, testler `pytest` ile doğrulanır.
- `make` hedefleri Linux/macOS/CI içindir; Windows'ta doğrudan `docker compose` ve `python -m` komutları kullanılır.
- İsim ve okul maskeleme kural/kalıp tabanlı sezgiseldir (heuristic); %100 doğruluk vaat edilmez, standart dışı ifadeler gözden kaçabilir. Bilinen sınırlar: 10 haneli ve 5 ile başlayan sayılar telefon sanılabilir; "Ali'yim" gibi kalıpsız isimler yakalanmaz.
- Gemini ücretsiz katmanında içerik Google tarafından ürün geliştirmede kullanılabilir. Geliştirme/test sahte veriyle yapılır, gerçek çocuklarla pilot öncesi ücretli katmana geçilmeli.
- İstemci (D7-r): mobilde matematik gösterimi WebView + KaTeX ile yapılır, web'de KaTeX doğrudan kullanılır. Performans sorunu çıkarsa SVG tabanlı render değerlendirilir.
- Expo yönetilen iş akışı (CNG) kullanılır; `ios/` ve `android/` klasörleri gerekmedikçe repoya girmez. Analitik/izleme SDK'sı (ör. Sentry, Firebase Analytics) eklenmez (Kural 5).
- Geliştirmede API adresi: `EXPO_PUBLIC_API_URL` verilmezse web'de `http://localhost:8000`, Expo Go'da Metro'yu çalıştıran makinenin adresi + `:8000` kullanılır; telefon ile bilgisayar aynı ağda olmalı.
- Eşleştirme bağlantısı (`/pair?child=…&code=…`) kodu URL'de taşır; kod tek kullanımlık ve 10 dk geçerli olduğu için kabul edildi (tarayıcı geçmişinde kalabilir).
- Golden set v1 (60 soru, 5–8. sınıf) sentetiktir ve öğretmen onayından geçmemiştir; Bölüm 11.2 gereği öğretmenlerle gözden geçirilip 200+ soruya genişletilmelidir.
- `POST /v1/problems` oturum (session) yapısı olmadan çalışır; oturumlar ve ipucu akışı M4/M6'da eklenir.
- Uygulama ikonları şimdilik Expo şablonundan; Hint.ai ikonu marka adı doğrulamasından (D14) sonra eklenir.
