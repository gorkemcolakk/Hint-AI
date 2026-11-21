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
# Model kullanılamadığında ya da her üretim reddedildiğinde verilen hazır ipuçları. Soru türüne
# göre seçilir; hiçbiri rakam içermez, bu yüzden cevabı ele veremez.
FALLBACK_HINTS: dict[ProblemKind, dict[int, str]] = {
    "equation": {
        0: _UNDERSTAND,
        1: "Bu bir denklem. Eşitliğin iki tarafına aynı işlemi yaparsak eşitlik bozulmaz. "
        "Bu kuralı burada nasıl kullanabiliriz?",
        2: "Bilinmeyeni yalnız bırakmak istiyoruz. Önce hangi terimden kurtulmak daha kolay olur?",
        3: "İlk adım olarak bilinmeyenin yanındaki toplama ya da çıkarmayı eşitliğin öbür "
        "tarafına geçirmeyi dene. Ne kaldığını bana yaz.",
        4: "Daha küçük sayılarla aynı türde bir denklem yaz ve çöz. Sonra aynı adımları kendi "
        "sorunda dene.",
    },
    "arithmetic": {
        0: _UNDERSTAND,
        1: "İşlem önceliğini hatırlayalım: önce parantez, sonra çarpma ve bölme, en son toplama "
        "ve çıkarma. Kesir varsa paydalara da bak.",
        2: "Önce hangi işlemi yapman gerektiğine karar ver ve yalnızca o kısmı hesapla.",
        3: "İşlemi parçalara ayır: ilk yapılması gereken kısmı bul, yalnızca onu hesapla ve "
        "sonucu bana yaz.",
        4: "Daha küçük sayılarla aynı türde bir işlem yaz ve çöz. Sonra aynı sırayı kendi "
        "sorunda uygula.",
    },
    "word": {
        0: _UNDERSTAND,
        1: "Bu soruda hangi bilgiler verilmiş? Onları kısa bir liste halinde yazmak işini "
        "kolaylaştırır.",
        2: "İstenen şeyi bulmak için hangi işlemi kullanman gerekiyor: toplama, çıkarma, çarpma "
        "mı, bölme mi? Neden?",
        3: "Soruyu bir işleme çevirmeyi dene: verilen sayıları ve aralarındaki ilişkiyi tek "
        "satırda yaz. Hesaplamayı sen yap.",
        4: "Aynı hikâyeyi daha küçük sayılarla düşün ve çöz. Sonra aynı yolu kendi sorunda dene.",
    },
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
    level: int, *, topic: str | None, support: bool, kind: ProblemKind = "word"
) -> str:
    text = FALLBACK_HINTS[kind][min(level, MAX_LEVEL)]
    if level == 1 and topic:
        text = f"Bu soru '{topic}' konusuyla ilgili. {text}"
    return f"{SUPPORT_LINE} {text}" if support else text


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
    """İpucu modeline giden kullanıcı mesajı (hint_v1 prompt'unun beklediği biçim)."""
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
    return cleaned[:600].strip()
