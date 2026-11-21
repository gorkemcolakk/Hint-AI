"""Kural tabanlı girdi güvenlik sınıflandırıcısı (Hint Engine adım 1).

Çocuğun yazdığı her metin (soru, mesaj, cevap) LLM'e gitmeden buradan geçer. Deterministiktir:
kriz durumunda model çağrılmaz ve önceden yazılmış sabit metin gösterilir (Bölüm 21.C: kriz
mesajları model improvizasyonuna bırakılmaz).

Çocuklar Türkçe karakter kullanmadan da yazar ("olmek istiyorum"); eşleştirme Türkçe
karakterleri sadeleştirilmiş metin üzerinde yapılır.

Bilinen sınır: anahtar kelime tabanlıdır, dolaylı anlatımları kaçırabilir. Gerçek çocuklarla
kullanımdan önce bir model tabanlı sınıflandırıcı ve uzman (psikolog/pedagog) onayı gerekir.
"""

import re
from dataclasses import dataclass
from typing import Literal

Category = Literal[
    "self_harm",
    "abuse_disclosure",
    "sexual_content",
    "violence",
    "bullying",
    "prompt_injection",
    "pii_share",
    "none",
]
Action = Literal["allow", "allow_with_notice", "redirect", "block_with_support"]


@dataclass(frozen=True)
class SafetyVerdict:
    category: Category
    action: Action
    severity: int  # 0 yok, 1 düşük, 2 orta, 3 kritik

    @property
    def blocks(self) -> bool:
        """Akış durur mu (LLM çağrılmaz, metin saklanmaz)?"""
        return self.action in ("redirect", "block_with_support")


SAFE = SafetyVerdict("none", "allow", 0)

_ASCII = str.maketrans("çğıöşüâîû", "cgiosuaiu")


def normalize(text: str) -> str:
    lowered = text.replace("I", "ı").replace("İ", "i").lower()
    ascii_text = lowered.translate(_ASCII)
    return re.sub(r"\s+", " ", ascii_text)


def _rx(*patterns: str) -> re.Pattern[str]:
    return re.compile("|".join(f"(?:{p})" for p in patterns))


# Kalıplar sadeleştirilmiş (ASCII) metin üzerinde çalışır.
_RULES: list[tuple[Category, Action, int, re.Pattern[str]]] = [
    (
        "self_harm",
        "block_with_support",
        3,
        _rx(
            r"kendimi (?:oldur|as|oldurece|oldurmek|yok et)",
            r"intihar",
            r"olmek ist",
            r"(?<![a-z])olsem(?![a-z])|olursem (?:herkes|kimse)",
            r"yasamak ist(?:emiyorum|emem)",
            r"yasamanin anlami yok",
            r"kendime zarar",
            r"(?:bilegimi|bileklerimi|kolumu|kendimi) kes",
            r"canima kiy",
            r"her seye son ver",
            r"keske dogmasaydim",
            r"\bkill myself\b|\bsuicide\b",
        ),
    ),
    (
        "abuse_disclosure",
        "block_with_support",
        3,
        _rx(
            r"beni (?:dov|dovuyor|dovdu|dover|darp)",
            r"bana (?:vuruyor|vurdu|vuruyorlar|siddet)",
            r"taciz",
            r"istismar",
            r"bana kotu (?:dokun|seyler yap)",
            r"kimseye (?:soyleme|anlatma) dedi",
            r"ozel yerlerime",
        ),
    ),
    (
        "sexual_content",
        "redirect",
        2,
        _rx(r"\bseks", r"\bporno", r"\bciplak", r"\bsex\b", r"\bnude"),
    ),
    (
        "violence",
        "redirect",
        2,
        _rx(
            r"(?<!kendimi )oldurece[gk]im",
            r"(?<!kendimi )oldurmek ist",
            r"bomba yap",
            r"silahla (?:vur|ates)",
            r"zarar verece[gk]im",
        ),
    ),
    (
        "bullying",
        "redirect",
        1,
        _rx(
            r"zorbalik",
            r"benimle (?:dalga geciyor|alay ediyor)",
            r"beni (?:disliyor|disliyorlar|asagiliyor)",
            r"herkes benimle dalga",
        ),
    ),
    (
        "prompt_injection",
        "allow_with_notice",
        1,
        _rx(
            r"cevab(?:i|ini)? ?(?:direkt|dogrudan|hemen)?\s*(?:soyle|ver|yaz|goster)",
            r"(?:sonucu|cozumu) (?:direkt |dogrudan |hemen )?(?:soyle|ver|yaz|goster)",
            r"(?:direkt|dogrudan|sadece) (?:cevab|sonuc)",
            r"(?:kurallari|talimatlari|onceki talimat|yonergeleri) (?:unut|gormezden gel|yok say)",
            r"(?:sistem|system) (?:promptu|prompt|mesaji)",
            r"ignore (?:all |the )?(?:previous|above) instructions",
            r"(?:ogretmenim|annem|babam|ebeveynim)(?: de)? izin verdi",
            r"sen artik (?:bir )?(?:ogretmen|hesap makinesi|cozucu|asistan|chatgpt|bot|insan)",
            r"(?:rol yap|gibi davran)",
            r"developer mode|jailbreak|\bdan modu",
            r"ipucu degil cevap",
        ),
    ),
]


def classify(text: str | None) -> SafetyVerdict:
    """En ağır eşleşen kategoriyi döner (kural sırası ağırlık sırasıdır)."""
    if not text:
        return SAFE
    normalized = normalize(text)
    for category, action, severity, pattern in _RULES:
        if pattern.search(normalized):
            return SafetyVerdict(category, action, severity)
    return SAFE
