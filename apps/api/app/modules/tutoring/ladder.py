"""İpucu merdiveni kuralları (Bölüm 6.2–6.3): seviyeler, yükselme ve güvenli yedek ipuçları."""

import re
from collections.abc import Mapping, Sequence
from typing import Any, Literal

LEVEL_NAMES = {
    0: "Anlama kontrolü",
    1: "Kavram yönü",
    2: "Strateji",
    3: "Kısmi adım",
    4: "Benzer çözümlü örnek",
}
# L5 (çözüm gösterimi) MVP'de kapalı (D4 kararı bekleniyor).
MAX_LEVEL = 4
# Doğrulanamayan çözümde ipucu temkinli tutulur; çözüm hiç yoksa yalnızca hazır ipuçları verilir.
MAX_LEVEL_BY_STATUS = {"verified": 4, "low_confidence": 2, "unverifiable": 2, "failed": 1}
WRONG_ATTEMPTS_BEFORE_ESCALATION = 2

_FRUSTRATION = re.compile(
    r"çok zor|yapamıyorum|yapamadım|sıkıldım|anlamıyorum|anlamadım|bıktım|nefret|imkansız|imkânsız",
    re.IGNORECASE,
)

SUPPORT_LINE = "Zorlanman çok normal, birlikte adım adım bakalım."

ProblemKind = Literal["equation", "arithmetic", "word"]

_UNDERSTAND = "Soruyu kendi cümlelerinle anlatır mısın? Bize ne verilmiş, ne bulmamız isteniyor?"
# Model kullanılamadığında ya da çözüm hiç olmadığında verilen rakamsız son çare ipuçları.
FALLBACK_HINTS: dict[ProblemKind, dict[int, str]] = {
    "equation": {
        0: _UNDERSTAND,
        1: "Bu bir denklem. Eşitliğin iki tarafına aynı ters işlemi yaparsak denge bozulmaz: "
        "toplamanın tersi çıkarma, çarpmanın tersi bölmedir. "
        "Burada önce hangi ters işlemi yapabiliriz?",
        2: "Bilinmeyenin (x'in) yanındaki sabit sayıdan kurtularak başlayalım: eklenmişse iki "
        "taraftan çıkar, çıkarılmışsa iki tarafa ekle. Sağ tarafta ne kalıyor?",
        3: "Sabit sayıyı öbür tarafa geçirdikten sonra elinde 'katsayı × x = bir sayı' kalır. "
        "Şimdi her iki tarafı x'in önündeki katsayıya bölerek x'i tek başına bırak!",
        4: "Aynı yapıda basit bir denklem düşün: önce bilinmeyenin yanındaki sabit sayıyı ters "
        "işlemle karşıya geçir, ardından kalan sonucu bilinmeyenin katsayısına böl.",
    },
    "arithmetic": {
        0: _UNDERSTAND,
        1: "İşlem önceliğini hatırlayalım: önce parantez içi, sonra çarpma veya bölme, en son "
        "toplama ve çıkarma yapılır. Kesir varsa önce paydaları eşitle.",
        2: "Sorudaki işlemlerden ilk yapılması gerekeni seç ve yalnızca o tek adımı hesapla.",
        3: "İlk işlemin bulduğun sonucunu soruda yerine yaz; geriye kalan son işlemi hesaplayarak "
        "cevaba ulaşabilirsin.",
        4: "İşlem sırasını adım adım uygula: önce parantez içini, sonra çarpma-bölmeyi, en son "
        "toplama-çıkarmayı ayrı satırlarda hesaplayarak ilerle.",
    },
    "word": {
        0: _UNDERSTAND,
        1: "Sorudaki sayıları ve neyi temsil ettiklerini kısaca alt alta not et; bizden istenen "
        "son miktarın ne olduğuna odaklan.",
        2: "Verilen miktar artıyor mu, azalıyor mu, yoksa eşit parçalara mı bölünüyor? Buna göre "
        "ilk yapman gereken işlemi (toplama, çıkarma, çarpma veya bölme) kur.",
        3: "İlk adımı hesaplayıp ara miktarı bul; ardından sorunun istediği son değeri bulmak "
        "için kalan tek işlemi uygula.",
        4: "Soruyu iki net adıma böl: önce verilen bilgiden ara miktarı hesapla, sonra sorunun "
        "istediği son değeri bulmak için ikinci işlemi tamamla.",
    },
}

# Çözüm bilindiğinde ve sızıntısız olduğunda L4 yedeği olarak kullanılan somut ikiz örnekler.
WORKED_L4_CANDIDATES: dict[ProblemKind, tuple[str, str]] = {
    "equation": (
        "Gel benzer bir örneği adım adım çözelim: 2x + 4 = 10 olsun. "
        "1. Adım: İki taraftan 4 çıkarırsak 2x = 6 kalır. "
        "2. Adım: 6'yı 2'ye bölersek x = 3 bulunur. "
        "Şimdi aynı iki adımı kendi denklemindeki sayılarla sırayla uygula!",
        "Gel benzer bir örneği adım adım çözelim: 5x - 7 = 28 olsun. "
        "1. Adım: İki tarafa 7 eklersek 5x = 35 olur. "
        "2. Adım: 35'i 5'e bölersek x = 7 bulunur. "
        "Şimdi aynı sırayla kendi denkleminde önce sabit sayıyı ayır, sonra katsayıya böl!",
    ),
    "arithmetic": (
        "Gel benzer bir örneği birlikte çözelim: 6 + 4 × 3 işleminde önce çarpma yapılır "
        "(4 × 3 = 12), sonra toplama yapılır (6 + 12 = 18). "
        "Şimdi aynı işlem sırasını kendi sorunda uygula!",
        "Gel benzer bir örneği birlikte çözelim: 25 - 5 × 3 işleminde önce çarpma "
        "yapılır (5 × 3 = 15), sonra çıkarma yapılır (25 - 15 = 10). "
        "Şimdi kendi sorunda aynı sırayı uygula!",
    ),
    "word": (
        "Gel benzer kısa bir örneğe bakalım: 80 TL'lik bir ürün %25 indirime girerse önce "
        "80'in dörtte birini buluruz (80 ÷ 4 = 20 TL indirim), sonra 80 - 20 = 60 TL öderiz. "
        "Şimdi kendi sorundaki sayılarla önce ara miktarı bul, sonra son işlemi tamamla!",
        "Gel benzer bir örneğe bakalım: Bir kitabın 1/7'sini sabah, 2/7'sini akşam okursak "
        "toplam 3/7'si okunur; geriye 7/7 - 3/7 = 4/7 kalır. "
        "Şimdi kendi sorundaki sayılarla adımları kur!",
    ),
}

UNVERIFIED_NOTE = "Bu soruda ben de tam emin değilim; öğretmenine de danışabilirsin."

# Sözel soru ayrımı için sayılmayan soru kelimeleri.
_QUESTION_WORDS = {
    "kaç",
    "kaçtır",
    "eder",
    "nedir",
    "sonucu",
    "işleminin",
    "ise",
    "bulunur",
    "olur",
    "değeri",
    "kaçı",
    "için",
    "ile",
    "toplamı",
    "farkı",
    "çarpımı",
    "bölümü",
}


def problem_kind(problem_text: str, sympy_check: Mapping[str, Any] | None) -> ProblemKind:
    """Yedek ipucu seçimi için kaba soru türü: denklem, saf işlem ya da sözel problem."""
    if sympy_check and sympy_check.get("type") == "solve":
        return "equation"
    words = re.findall(r"[a-zçğıöşüâîû]{3,}", problem_text.lower())
    content_words = [word for word in words if word not in _QUESTION_WORDS]
    return "word" if len(content_words) >= 3 else "arithmetic"


def max_level_for(status: str) -> int:
    return MAX_LEVEL_BY_STATUS.get(status, 1)


def is_frustrated(message: str | None) -> bool:
    return bool(message and _FRUSTRATION.search(message))


def next_level(current: int | None, *, status: str, frustrated: bool) -> int:
    """Bir sonraki ipucu seviyesi. İlk ipucu L0'dır; zorlanma sinyali bir seviye atlatır."""
    level = 0 if current is None else current + 1
    if frustrated and current is None:
        level = 1
    return min(level, max_level_for(status))


def fallback_hint(
    level: int,
    *,
    topic: str | None,
    support: bool,
    kind: ProblemKind = "word",
) -> str:
    clamped = min(level, MAX_LEVEL)
    text = FALLBACK_HINTS[kind][clamped]
    if clamped == 1 and topic:
        text = f"Bu soru '{topic}' konusuyla ilgili. {text}"
    return f"{SUPPORT_LINE} {text}" if support else text


def worked_l4_candidates(kind: ProblemKind, *, support: bool) -> list[str]:
    return [
        f"{SUPPORT_LINE} {example}" if support else example
        for example in WORKED_L4_CANDIDATES[kind]
    ]


def build_hint_request(
    *,
    problem_text: str,
    steps: Sequence[str],
    final_answer: str,
    level: int,
    age_band: str,
    previous_hints: Sequence[str],
    student_message: str | None,
    frustrated: bool,
) -> str:
    """İpucu modeline giden kullanıcı mesajı (hint_v3 prompt'unun beklediği biçim)."""
    lines = [
        f"SORU: {problem_text}",
        "GİZLİ ÇÖZÜM ADIMLARI:",
        *(f"- {step}" for step in steps),
        f"NİHAİ CEVAP (ASLA YAZMA): {final_answer}",
        f"SEVİYE: L{level} ({LEVEL_NAMES[level]})",
        f"YAŞ BANDI: {age_band}",
        "ÖNCEKİ İPUÇLARI:",
        *(f"- {hint}" for hint in previous_hints[-3:]),
    ]
    if not previous_hints:
        lines.append("- (yok)")
    if student_message:
        lines.append(f"ÖĞRENCİNİN MESAJI: {student_message}")
    if frustrated:
        lines.append("NOT: Öğrenci zorlandığını söyledi; önce kısa bir destek cümlesi yaz.")
    return "\n".join(lines)


def clean_hint(text: str) -> str:
    """Model çıktısındaki tırnak/başlık artıklarını temizler ve uzunluğu sınırlar."""
    cleaned = text.strip().strip('"“”').strip()
    cleaned = re.sub(r"^(?:ipucu|L\d)\s*[:\-–]\s*", "", cleaned, flags=re.IGNORECASE)
    return cleaned[:800].strip()
