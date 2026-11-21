"""Kural tabanlı cevap sızıntısı kontrolü (Hint Engine adım 7a).

Deterministiktir ve her ipucunda çalışır; LLM yargıç (7b) bunun yerine değil, üstüne eklenir.
Kontrol edilenler:
- Nihai cevabın değeri ipucunda rakamla (5, 0,75, 3/4), yazıyla (beş, yirmi beş) veya kök
  ifadesiyle (2√3) geçiyor mu. İşaret önemsizdir: -7 cevabında "7" de sızıntıdır.
- Cevap değeri soru metninde zaten geçiyorsa (ör. "x + 5 = 10" ve cevap 5) sayının görünmesi
  tek başına sızıntı sayılmaz; "x = 5", "cevap 5", "5 olur" gibi atama kalıpları aranır.
- L0–L2'de çözüm adımlarındaki kritik ara sonuçlar ("3x = 15" adımındaki 15) da yasaktır.
  L3 ara değer verebilir, L4 farklı sayılarla örnek çözer; ikisinde yalnızca nihai cevap yasaktır.

Bilinen sınırlar (yargıç kapatır): "üçte bir" gibi yazıyla kesirler ve tek başına "bir"/"on"
sözcükleri ek almış halleriyle yakalanmaz; dolaylı anlatımlar ("ikinin iki katı") yakalanmaz.
"""

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

import sympy

from app.modules.problems.verify import parse_answers

# Rakamla yazılmış sayı: 15, 0,75, 2.5, 3/4 (önünde/arkasında rakam olmamalı).
_NUMBER = re.compile(r"(?<![\d.,])(\d+(?:[.,]\d+)?)(?:\s*/\s*(\d+))?(?![\d])")
_STEP_RESULT = re.compile(r"=\s*(-?\d+(?:[.,]\d+)?(?:\s*/\s*\d+)?)")
_LETTERS = "a-zçğıöşü"
_ASSIGNMENT_BEFORE = re.compile(
    rf"(?:(?<![{_LETTERS}])[a-z]\s*=\s*|(?:cevap|sonuç|yanıt)[{_LETTERS}]*\s*[:=]?\s*)-?$"
)
_ASSIGNMENT_AFTER = re.compile(
    r"^\s*(?:'?\s*(?:dir|dır|dur|dür|tir|tır|tur|tür)\b|olur|bulunur|çıkar|eder|'?y?[ea] eşit)"
)

_ONES = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
_TENS = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
# Çok yaygın sözcükler: yalnızca tek başına geçtiklerinde sayılır (ek almış halleri değil).
_EXACT_ONLY_WORDS = {"bir", "on"}
_CASE_SUFFIX = r"(?:'?(?:y?[eaıiuü]|y?[ae]|d[ae]|t[ae]|d[ae]n|t[ae]n|l[ae]|y?l[ae]))?"

MAX_FORBIDDEN_WORD_VALUE = 999


@dataclass(frozen=True)
class LeakResult:
    ok: bool
    reasons: list[str] = field(default_factory=list)


def _turkish_lower(text: str) -> str:
    return text.replace("I", "ı").replace("İ", "i").lower()


def turkish_number_words(n: int) -> str:
    """0–999 arası tam sayının Türkçe yazılışı (ör. 125 → 'yüz yirmi beş')."""
    if n == 0:
        return "sıfır"
    hundreds, rest = divmod(n, 100)
    tens, ones = divmod(rest, 10)
    parts = []
    if hundreds:
        parts.append("yüz" if hundreds == 1 else f"{_ONES[hundreds]} yüz")
    if tens:
        parts.append(_TENS[tens])
    if ones:
        parts.append(_ONES[ones])
    return " ".join(parts)


def _to_number(text: str) -> Any:
    """'0,75' / '3/4' / '15' metnini SymPy sayısına çevirir (işaretsiz)."""
    cleaned = text.replace(" ", "").replace(",", ".").lstrip("-")
    if "/" in cleaned:
        numerator, denominator = cleaned.split("/", 1)
        if int(denominator) == 0:
            return None
        return sympy.Rational(sympy.Rational(numerator), sympy.Rational(denominator))
    return sympy.Rational(cleaned)


def _numbers_with_spans(text: str) -> list[tuple[Any, int, int]]:
    found = []
    for match in _NUMBER.finditer(text):
        raw = match.group(0)
        try:
            value = _to_number(raw)
        except (ValueError, TypeError, ZeroDivisionError):
            continue
        if value is not None:
            found.append((value, match.start(), match.end()))
    return found


def _same_magnitude(a: Any, b: Any) -> bool:
    try:
        if sympy.Abs(a) == sympy.Abs(b):
            return True
        # Yaklaşık ondalık yazım (ör. √2 için 1,41) da sızıntıdır.
        fa, fb = abs(float(a)), abs(float(b))
    except (TypeError, ValueError):
        return False
    return bool(not fa.is_integer() or not fb.is_integer()) and abs(fa - fb) < 0.005 * max(1, fb)


def _contains(values: Iterable[Any], target: Any) -> bool:
    return any(_same_magnitude(value, target) for value in values)


def _word_leaks(hint_lower: str, value: Any, *, require_assignment: bool) -> list[str]:
    if not (value.is_integer and abs(int(value)) <= MAX_FORBIDDEN_WORD_VALUE):
        return []
    words = turkish_number_words(abs(int(value)))
    boundary = rf"(?<![{_LETTERS}])"
    if words in _EXACT_ONLY_WORDS:
        pattern = rf"{boundary}{words}(?![{_LETTERS}])"
    else:
        pattern = rf"{boundary}{re.escape(words)}{_CASE_SUFFIX}(?![{_LETTERS}])"
    for match in re.finditer(pattern, hint_lower):
        if not require_assignment or _is_assignment(hint_lower, match.start(), match.end()):
            return [f"number_word:{words}"]
    return []


def _radical_leaks(hint_lower: str, value: Any) -> list[str]:
    if value.is_rational or not value.has(sympy.Pow):
        return []
    normalized = re.sub(r"\s+|\*", "", hint_lower)
    normalized = re.sub(r"(?:karekök|kök)\(?(\d+)\)?", r"sqrt(\1)", normalized)
    normalized = re.sub(r"√\(?(\d+)\)?", r"sqrt(\1)", normalized)
    target = str(sympy.Abs(value)).replace("*", "").replace(" ", "")
    return [f"radical:{target}"] if target in normalized else []


def _is_assignment(hint_lower: str, start: int, end: int) -> bool:
    before, after = hint_lower[max(0, start - 20) : start], hint_lower[end : end + 15]
    return bool(_ASSIGNMENT_BEFORE.search(before) or _ASSIGNMENT_AFTER.search(after))


def intermediate_values(steps: Sequence[str]) -> list[Any]:
    """Çözüm adımlarında '=' işaretinden sonra gelen ara sonuçlar."""
    values = []
    for step in steps:
        for match in _STEP_RESULT.finditer(step):
            try:
                value = _to_number(match.group(1))
            except (ValueError, TypeError, ZeroDivisionError):
                continue
            if value is not None:
                values.append(value)
    return values


def check_hint(
    hint: str,
    *,
    level: int,
    final_answer: str,
    steps: Sequence[str],
    problem_text: str,
) -> LeakResult:
    """İpucunun nihai cevabı (ve L0–L2'de kritik ara değerleri) ele verip vermediğini denetler."""
    try:
        answers = parse_answers(final_answer)
    except Exception:
        # Cevap okunamıyorsa neyin yasak olduğu bilinemez: güvenli taraf.
        return LeakResult(False, ["final_answer_unparseable"])

    hint_lower = _turkish_lower(hint)
    hint_numbers = _numbers_with_spans(hint_lower)
    problem_numbers = [value for value, _, _ in _numbers_with_spans(_turkish_lower(problem_text))]
    reasons: list[str] = []

    for answer in answers:
        label = str(sympy.Abs(answer))
        in_problem = _contains(problem_numbers, answer)
        for value, start, end in hint_numbers:
            if not _same_magnitude(value, answer):
                continue
            if not in_problem or _is_assignment(hint_lower, start, end):
                reasons.append(f"final_answer:{label}")
                break
        reasons += _word_leaks(hint_lower, answer, require_assignment=in_problem)
        reasons += _radical_leaks(hint_lower, answer)

    if level <= 2:
        for value in intermediate_values(steps):
            if _contains(problem_numbers, value) or _contains(answers, value):
                continue
            if any(_same_magnitude(found, value) for found, _, _ in hint_numbers):
                reasons.append(f"intermediate:{sympy.Abs(value)}")

    unique = list(dict.fromkeys(reasons))
    return LeakResult(not unique, unique)
