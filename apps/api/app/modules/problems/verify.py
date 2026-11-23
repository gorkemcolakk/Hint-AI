"""SymPy ile gizli çözüm doğrulaması.

LLM'in ürettiği ifadeler güvenilmez girdidir (soru metnindeki talimatlarla yönlendirilebilir).
SymPy'ın ayrıştırıcısı içeride Python eval kullandığı için yalnızca izinli karakterlerden,
tek harfli değişkenlerden ve izinli fonksiyonlardan oluşan kısa ifadeler ayrıştırılır; büyük
üsler gibi işlemciyi kilitleyebilecek girdiler reddedilir.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

import sympy
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

MAX_EXPRESSION_LENGTH = 200
_ALLOWED_CHARS = re.compile(r"^[0-9A-Za-z\s+\-*/^().,=]+$")
_FUNCTIONS: dict[str, Any] = {
    "sqrt": sympy.sqrt,
    "gcd": sympy.gcd,
    "lcm": sympy.lcm,
    "abs": sympy.Abs,
    "pi": sympy.pi,
}
_TRANSFORMATIONS = (*standard_transformations, implicit_multiplication_application, convert_xor)
# Büyük üs (ör. 9^99999) veya iç içe üs (2^3^4) hesaplamayı kilitleyebilir.
_BIG_EXPONENT = re.compile(r"\^\s*\(?\s*-?\d{4,}")
_NESTED_EXPONENT = re.compile(r"\^[^+\-*/=,]*\^")
_BIG_NUMBER = re.compile(r"\d{13,}")

VerificationStatus = Literal["verified", "mismatch", "unverifiable"]


class UnsafeExpressionError(ValueError):
    """İfade izinli biçimin dışında; ayrıştırılmadan reddedildi."""


@dataclass(frozen=True)
class VerificationResult:
    status: VerificationStatus
    note: str


def parse_math(text: str) -> Any:
    """Güvenlik kontrolünden geçen kısa bir matematik ifadesini SymPy nesnesine çevirir."""
    cleaned = text.strip().replace("**", "^").replace("×", "*").replace("÷", "/").replace("−", "-")
    if not cleaned or len(cleaned) > MAX_EXPRESSION_LENGTH:
        raise UnsafeExpressionError("ifade boş ya da çok uzun")
    if not _ALLOWED_CHARS.match(cleaned):
        raise UnsafeExpressionError("izin verilmeyen karakter")
    if cleaned.count("^") > 4 or _BIG_EXPONENT.search(cleaned) or _NESTED_EXPONENT.search(cleaned):
        raise UnsafeExpressionError("üs çok büyük ya da iç içe")
    if _BIG_NUMBER.search(cleaned):
        raise UnsafeExpressionError("sayı çok büyük")

    local_dict: dict[str, Any] = {}
    for name in set(re.findall(r"[A-Za-z]+", cleaned)):
        if name in _FUNCTIONS:
            local_dict[name] = _FUNCTIONS[name]
        elif len(name) == 1:
            # E, I, N, S gibi tek harfler SymPy'da özel anlam taşır; hepsi düz değişken olsun.
            local_dict[name] = sympy.Symbol(name)
        else:
            raise UnsafeExpressionError(f"bilinmeyen isim: {name}")

    global_dict: dict[str, Any] = {
        "__builtins__": {},
        "Integer": sympy.Integer,
        "Float": sympy.Float,
        "Rational": sympy.Rational,
        "Symbol": sympy.Symbol,
        "Function": sympy.Function,
    }
    return parse_expr(
        cleaned, local_dict=local_dict, global_dict=global_dict, transformations=_TRANSFORMATIONS
    )


def _same(a: Any, b: Any) -> bool:
    difference = sympy.simplify(a - b)
    if difference == 0:
        return True
    return bool(difference.is_number and abs(float(difference)) < 1e-9)


def parse_answers(final_answer: str) -> list[Any]:
    """'x = 5' veya '7; -7' biçimindeki cevap metnini değer listesine çevirir."""
    values = []
    for part in final_answer.split(";"):
        value = part.rsplit("=", 1)[-1].strip()
        if value:
            values.append(parse_math(value))
    if not values:
        raise UnsafeExpressionError("cevap boş")
    return values


def answers_match(expected: str, actual: str) -> bool:
    """İki cevap metni aynı değer kümesini mi gösteriyor (sıra ve yazım biçimi önemsiz)."""
    try:
        left, right = parse_answers(expected), parse_answers(actual)
    except Exception:
        return False
    return len(left) == len(right) and all(any(_same(a, b) for b in right) for a in left)


def _expected_values(check: Mapping[str, Any]) -> list[Any]:
    """SymPy kontrolünden bağımsız sonucu hesaplar; biçim geçersizse ValueError fırlatır."""
    kind = check.get("type")
    if kind == "solve":
        equation = str(check.get("equation", ""))
        variable = str(check.get("variable", ""))
        if equation.count("=") != 1 or not re.fullmatch(r"[A-Za-z]", variable):
            raise ValueError("denklem biçimi geçersiz")
        lhs, rhs = (parse_math(side) for side in equation.split("="))
        return list(sympy.solve(sympy.Eq(lhs, rhs), sympy.Symbol(variable)))
    if kind == "evaluate":
        return [parse_math(str(check.get("expression", "")))]
    raise ValueError(f"bilinmeyen kontrol türü: {kind}")


def sympy_answer(check: Mapping[str, Any] | None) -> str | None:
    """SymPy'ın bağımsız bulduğu cevap ('5' ya da '7; -7'); hesaplanamazsa None."""
    if not check:
        return None
    try:
        values = _expected_values(check)
    except Exception:
        return None
    return "; ".join(str(value) for value in values) if values else None


def verify_solution(check: Mapping[str, Any] | None, final_answer: str) -> VerificationResult:
    """Çözümün nihai cevabını SymPy ile bağımsız olarak hesaplanan sonuçla karşılaştırır."""
    if not check:
        return VerificationResult("unverifiable", "SymPy kontrolü tanımlanmamış")
    try:
        answers = parse_answers(final_answer)
        expected = _expected_values(check)
    except ValueError as exc:
        return VerificationResult("unverifiable", str(exc))
    except Exception as exc:
        return VerificationResult("unverifiable", f"ayrıştırılamadı: {type(exc).__name__}")

    if not expected:
        return VerificationResult("unverifiable", "SymPy çözüm bulamadı")
    matched = len(answers) == len(expected) and all(
        any(_same(answer, value) for value in expected) for answer in answers
    )
    if matched:
        return VerificationResult("verified", "SymPy sonucu ile eşleşti")
    return VerificationResult("mismatch", f"SymPy sonucu: {', '.join(str(v) for v in expected)}")
