"""PII Maskeleme Modülü.

KVKK ve çocuk güvenliği uyumu için öğrenci girdisindeki kişisel verileri
(TCKN, telefon, e-posta, IBAN, ad/okul gibi kalıplar) maskeler.
"""

import re
from dataclasses import dataclass


class MaskedText(str):
    """Yalnızca maskeleme katmanı tarafından üretilmiş güvenli metin tipi."""

    pass


class TrustedText(str):
    """Uygulamanın kendi yazdığı, kullanıcı girdisi içermeyen metin (system prompt'lar).

    Maskelenmez; yalnızca system rolündeki mesajlarda kullanılabilir.
    """

    pass


@dataclass(frozen=True)
class MaskResult:
    masked_text: MaskedText
    detected_types: list[str]
    has_pii: bool


def is_valid_tckn(val: str) -> bool:
    """11 haneli TCKN algoritma ve checksum doğrulaması."""
    if len(val) != 11 or not val.isdigit():
        return False
    if val[0] == "0":
        return False

    digits = [int(c) for c in val]
    odd_sum = sum(digits[0:9:2])  # 1, 3, 5, 7, 9. haneler
    even_sum = sum(digits[1:8:2])  # 2, 4, 6, 8. haneler

    d10 = ((odd_sum * 7) - even_sum) % 10
    if d10 != digits[9]:
        return False

    d11 = sum(digits[:10]) % 10
    if d11 != digits[10]:
        return False

    return True


def is_valid_tr_iban(val: str) -> bool:
    """TR IBAN format ve mod 97 checksum doğrulaması."""
    clean = re.sub(r"\s+", "", val).upper()
    if len(clean) != 26 or not clean.startswith("TR") or not clean[2:].isdigit():
        return False

    # İlk 4 karakteri sona al
    reordered = clean[4:] + clean[:4]
    num_str = ""
    for char in reordered:
        if char.isdigit():
            num_str += char
        else:
            num_str += str(ord(char) - ord("A") + 10)

    try:
        return int(num_str) % 97 == 1
    except ValueError:
        return False


# Regex Kalıpları
_EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# +90, 0090, 0 veya doğrudan 5xx formatları (boşluklu, tireli veya bitişik)
_PHONE_REGEX = re.compile(
    r"(?<!\d)(?:\+90|0090|0)?[\s-]*(5\d{2})[\s-]*(\d{3})[\s-]*(\d{2})[\s-]*(\d{2})(?!\d)"
)

# 11 haneli sayı adayları (TCKN adayı)
_TCKN_CANDIDATE_REGEX = re.compile(r"(?<!\d)[1-9]\d{10}(?!\d)")

# TR IBAN adayı
_IBAN_CANDIDATE_REGEX = re.compile(r"(?i)\bTR[\s\d]{24,32}\b")

# Sezgisel İsim Kalıpları
# "adım" Türkçede hem "benim adım" hem "ilk adım" anlamına gelir. Belirsiz olmayan
# kalıplar ("ismim", "benim adım") her zaman isim sayılır; tek başına "adım" ise yalnızca
# büyük harfle başlayan bir kelimeden önce ya da cümle başında, adım bağlamı kelimesi
# gelmiyorsa isim sayılır.
_LETTER = "A-Za-zÇĞİÖŞÜçğıöşü"
_UPPER = "A-ZÇĞİÖŞÜ"
_ANY_NAME = rf"[{_LETTER}]+"
_CAP_NAME = rf"[{_UPPER}][{_LETTER}]*"
_STEP_WORDS = (
    r"(?:ne|nedir|neydi|nasıl|hangisi|olarak|için|sonra|sonrası|sonraki|önce|geri|ileri|"
    r"atarak|atalım|at|adım|daha|bu|şu|o|bir|ilk|son|var|yok|doğru|yanlış|gibi|ile|de|da|"
    r"mı|mi)"
)
# Ad + en fazla iki büyük harfli kelime (ikinci ad, soyad); "Kerem Can Aydın" tamamen maskelenir.
_SURNAMES = rf"(?:\s+{_CAP_NAME}){{0,2}}"
_NAME_EXPLICIT_REGEX = re.compile(
    rf"(?i:\b(?:benim\s+(?:adım|ismim)|ismim))\s+({_ANY_NAME}{_SURNAMES})"
)
_NAME_ADIM_CAPITAL_REGEX = re.compile(
    rf"(?i:\badım)\s+(?!(?i:{_STEP_WORDS})\b)({_CAP_NAME}{_SURNAMES})"
)
_NAME_ADIM_SENTENCE_START_REGEX = re.compile(
    rf"(?:^|(?<=[.!?]\s)|(?<=\n))(?i:adım)\s+(?!(?i:{_STEP_WORDS})\b)({_ANY_NAME})"
)
_NAME_BANA_REGEX = re.compile(rf"(?i:\bbana)\s+({_ANY_NAME})\s+(?i:derler)\b")

# Sezgisel Okul Kalıpları (1-3 kelime + okul türü; zamirler hariç)
_SCHOOL_STOP_WORDS = r"(?:ben|biz|sen|benim|bizim|o|şu|bu)"
_SCHOOL_REGEX = re.compile(
    r"(?i)\b(?!"
    + _SCHOOL_STOP_WORDS
    + r"\b)([A-ZÇĞİÖŞÜa-zçğıöşü0-9]+(?:\s+(?!"
    + _SCHOOL_STOP_WORDS
    + r"\b)[A-ZÇĞİÖŞÜa-zçğıöşü0-9]+){0,2}\s+"
    r"(?:İlkokulu|İlkokul|Ortaokulu|Ortaokul|Fen Lisesi|Anadolu Lisesi|Lisesi|Lise|Koleji|Kolej))\b"
)


def mask_pii(text: str) -> MaskResult:
    """Metin içindeki kişisel verileri maskeler ve tespit edilen türleri döner."""
    if not text:
        return MaskResult(masked_text=MaskedText(""), detected_types=[], has_pii=False)

    detected: list[str] = []
    result = text

    # 1. E-posta maskeleme
    if _EMAIL_REGEX.search(result):
        detected.append("E-POSTA")
        result = _EMAIL_REGEX.sub("[E-POSTA]", result)

    # 2. IBAN maskeleme (doğrulamalı)
    def _replace_iban(match: re.Match[str]) -> str:
        matched_str = match.group(0)
        if is_valid_tr_iban(matched_str):
            if "IBAN" not in detected:
                detected.append("IBAN")
            return "[IBAN]"
        return matched_str

    result = _IBAN_CANDIDATE_REGEX.sub(_replace_iban, result)

    # 3. Telefon maskeleme
    if _PHONE_REGEX.search(result):
        detected.append("TELEFON")
        result = _PHONE_REGEX.sub("[TELEFON]", result)

    # 4. TCKN maskeleme (yalnızca geçerli olanlar)
    def _replace_tckn(match: re.Match[str]) -> str:
        matched_str = match.group(0)
        if is_valid_tckn(matched_str):
            if "TCKN" not in detected:
                detected.append("TCKN")
            return "[TCKN]"
        return matched_str

    result = _TCKN_CANDIDATE_REGEX.sub(_replace_tckn, result)

    # 5. Sezgisel okul maskeleme
    if _SCHOOL_REGEX.search(result):
        detected.append("OKUL")
        result = _SCHOOL_REGEX.sub("[OKUL]", result)

    # 6. Sezgisel ad maskeleme (yalnızca yakalanan ad değiştirilir, kalıbın kalanı korunur)
    def _replace_name(match: re.Match[str]) -> str:
        if "ISIM" not in detected:
            detected.append("ISIM")
        start, end = match.start(1) - match.start(0), match.end(1) - match.start(0)
        full = match.group(0)
        return full[:start] + "[ISIM]" + full[end:]

    for name_regex in (
        _NAME_EXPLICIT_REGEX,
        _NAME_ADIM_CAPITAL_REGEX,
        _NAME_ADIM_SENTENCE_START_REGEX,
        _NAME_BANA_REGEX,
    ):
        result = name_regex.sub(_replace_name, result)

    return MaskResult(
        masked_text=MaskedText(result),
        detected_types=detected,
        has_pii=len(detected) > 0,
    )
