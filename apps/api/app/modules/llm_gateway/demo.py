"""Yerel demo sağlayıcısı (LLM_PROVIDER=demo): API anahtarı ve kota olmadan gerçekçi akış.

Gerçek bir dil modeli değildir. Gizli çözüm isteğinde sorudaki basit denklemi veya işlemi SymPy
ile çözer; ipucu isteğinde seviyeye göre şablon ipucu yazar. Sözel problemleri çözemez (soru
'failed' olur ve hazır ipuçlarıyla devam edilir). Yalnızca geliştirme ve demo içindir.
"""

import json
import re
from typing import Any

import sympy

from app.modules.llm_gateway.providers import BaseLLMProvider, LLMMessage, LLMResponse
from app.modules.problems.verify import parse_math

_MATH_TOKEN = r"(?:\d+(?:[.,]\d+)?|(?<![a-zçğıöşü])[a-z](?![a-zçğıöşü])|[+\-*/^()=×÷:])"
_MATH_CHUNK = re.compile(rf"{_MATH_TOKEN}(?:\s*{_MATH_TOKEN})*", re.IGNORECASE)

_EQUATION_EXAMPLES = [
    ("2x + 3 = 11", "iki taraftan 3 çıkarırız: 2x = 8", "iki tarafı 2'ye böleriz: x = 4", 4),
    ("4x - 2 = 10", "iki tarafa 2 ekleriz: 4x = 12", "iki tarafı 4'e böleriz: x = 3", 3),
    ("5x + 1 = 31", "iki taraftan 1 çıkarırız: 5x = 30", "iki tarafı 5'e böleriz: x = 6", 6),
]
_ARITHMETIC_EXAMPLES = [
    ("2 + 3 × 4", "önce çarpma yapılır: 3 × 4 = 12", "sonra toplama: 2 + 12 = 14", 14),
    ("20 - 6 : 2", "önce bölme yapılır: 6 : 2 = 3", "sonra çıkarma: 20 - 3 = 17", 17),
    ("(5 + 3) × 2", "önce parantez: 5 + 3 = 8", "sonra çarpma: 8 × 2 = 16", 16),
]


def _extract_math(text: str) -> str | None:
    """Metindeki en uzun matematik parçası (rakam içeren ve işlem barındıran)."""
    chunks = [c.strip() for c in _MATH_CHUNK.findall(text)]
    candidates = [c for c in chunks if re.search(r"\d", c) and re.search(r"[+\-*/^=×÷:]", c)]
    if not candidates:
        return None
    best = max(candidates, key=len)
    best = re.sub(r"(\d),(\d)", r"\1.\2", best).replace(":", "/").replace("×", "*")
    return best.replace("÷", "/").strip(" =")


def _fmt(value: Any) -> str:
    return str(value).replace("**", "^")


def solve_text(text: str) -> dict[str, Any] | None:
    expression = _extract_math(text)
    if expression is None:
        return None
    try:
        if expression.count("=") == 1:
            lhs_text, rhs_text = expression.split("=")
            lhs, rhs = parse_math(lhs_text), parse_math(rhs_text)
            symbols = sorted((lhs - rhs).free_symbols, key=str)
            if len(symbols) != 1:
                return None
            x = symbols[0]
            solutions = sympy.solve(sympy.Eq(lhs, rhs), x)
            if not solutions:
                return None
            expr = sympy.expand(lhs - rhs)
            steps = []
            if sympy.degree(expr, x) == 1:
                a, b = expr.coeff(x, 1), expr.subs(x, 0)
                steps = [
                    f"Sabit terimleri karşı tarafa topla: {_fmt(a)}{x} = {_fmt(-b)}",
                    f"Her iki tarafı {_fmt(a)}'e böl: {x} = {_fmt(solutions[0])}",
                ]
            else:
                steps = [f"Denklemi {x} için çöz"]
            return {
                "grade": None,
                "topic": "birinci dereceden denklem" if len(steps) == 2 else "denklem",
                "steps": steps,
                "final_answer": "; ".join(_fmt(s) for s in solutions),
                "sympy_check": {"type": "solve", "equation": expression, "variable": str(x)},
            }
        if expression.count("=") == 0:
            value = sympy.nsimplify(parse_math(expression))
            if value.free_symbols:
                return None
            return {
                "grade": None,
                "topic": "dört işlem",
                "steps": ["İşlem önceliğine dikkat ederek hesapla"],
                "final_answer": _fmt(value),
                "sympy_check": {"type": "evaluate", "expression": expression},
            }
    except Exception:
        return None
    return None


def _field(message: str, name: str) -> str:
    match = re.search(rf"^{name}: (.*)$", message, re.MULTILINE)
    return match.group(1).strip() if match else ""


def write_hint(message: str, variant: int) -> str:
    level_match = re.search(r"^SEVİYE: L(\d)", message, re.MULTILINE)
    level = int(level_match.group(1)) if level_match else 0
    equation = "=" in _field(message, "SORU")
    steps = re.findall(r"^- (.+)$", message.split("NİHAİ CEVAP")[0], re.MULTILINE)
    support = (
        "Zorlanman çok normal, birlikte bakalım. " if "NOT: Öğrenci zorlandı" in message else ""
    )

    if level == 0:
        text = (
            "Bu soruda bize ne verilmiş, ne bulmamız isteniyor? Kendi cümlelerinle anlatır mısın?"
        )
    elif level == 1:
        text = (
            "Bir eşitliğin iki tarafına aynı işlemi yaparsak eşitlik bozulmaz. "
            "Bu kuralı burada nasıl kullanabiliriz?"
            if equation
            else "İşlem önceliğini hatırlayalım: önce parantez, sonra çarpma ve bölme, en son "
            "toplama ve çıkarma. Sorunda hangileri var?"
        )
    elif level == 2:
        text = (
            "Bilinmeyeni yalnız bırakmak istiyoruz. Önce hangi sayıdan kurtulmak daha kolay olur?"
            if equation
            else "Önce hangi işlemi yapman gerektiğine karar ver ve sadece o kısmı hesapla."
        )
    elif level == 3 and steps:
        first = steps[0][0].lower() + steps[0][1:]
        text = f"İlk adımı birlikte yapalım: {first}. Şimdi bir sonraki adımı sen dene."
    else:
        examples = _EQUATION_EXAMPLES if equation else _ARITHMETIC_EXAMPLES
        problem, step1, step2, _ = examples[variant % len(examples)]
        text = (
            f"Benzer bir örneğe bakalım: {problem}. Önce {step1}. Sonra {step2}. "
            "Şimdi aynı adımları kendi sorunda dene."
        )
    return support + text


class DemoLLMProvider(BaseLLMProvider):
    """Kota harcamayan, kurallı yerel demo sağlayıcısı."""

    # Gateway her çağrıda yeni sağlayıcı oluşturur; yeniden üretimde farklı örnek seçilebilsin
    # diye sayaç sınıf düzeyindedir.
    call_count = 0

    async def generate(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        self._validate_messages(messages)
        system = next((m.content for m in messages if m.role == "system"), "")
        user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        DemoLLMProvider.call_count += 1
        if "matematik çözücüsü" in system:
            solved = solve_text(user)
            content = json.dumps(solved, ensure_ascii=False) if solved else "Çözemedim."
        elif "ipucu yazarı" in system:
            content = write_hint(user, DemoLLMProvider.call_count)
        elif "kalite denetçisi" in system:
            # Demo yargıç: kural katmanını geçen şablon ipuçlarını onaylar.
            content = json.dumps({"leak": False, "reason": "demo", "severity": 0})
        else:
            content = "Demo sağlayıcısı bu isteği tanımıyor."
        return LLMResponse(content=content, input_tokens=0, output_tokens=0, latency_ms=5)
