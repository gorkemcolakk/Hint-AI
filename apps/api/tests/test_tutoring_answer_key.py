"""Düşük güvenli sorularda cevap anahtarı ve yasaklı cevaplar.

SymPy modelin cevabıyla çeliştiğinde (low_confidence) modelin cevabı muhtemelen yanlıştır:
öğrencinin cevabı SymPy'ın sonucuyla karşılaştırılmalı, ipucunda iki cevap da yasak olmalıdır.
"""

from app.modules.problems.models import HiddenSolution, Problem
from app.modules.problems.verify import answers_match, sympy_answer
from app.modules.tutoring.leak import check_hint
from app.modules.tutoring.service import answer_key, forbidden_answers

PROBLEM_TEXT = "3x + 5 = 20 ise x kaçtır?"
CHECK = {"type": "solve", "equation": "3*x + 5 = 20", "variable": "x"}


def _pair(status: str, model_answer: str) -> tuple[Problem, HiddenSolution]:
    problem = Problem(status=status, masked_text=PROBLEM_TEXT)
    solution = HiddenSolution(final_answer=model_answer, steps=[], sympy_check=CHECK)
    return problem, solution


def test_sympy_answer_is_computed_independently() -> None:
    assert sympy_answer(CHECK) == "5"
    assert sympy_answer({"type": "solve", "equation": "x^2 = 49", "variable": "x"}) == "-7; 7"
    assert sympy_answer(None) is None
    assert sympy_answer({"type": "evaluate", "expression": "__import__(1)"}) is None


def test_low_confidence_attempt_is_checked_against_sympy() -> None:
    problem, solution = _pair("low_confidence", model_answer="6")
    key = answer_key(problem, solution)
    assert answers_match(key, "5")
    assert not answers_match(key, "6")


def test_verified_attempt_uses_model_answer() -> None:
    problem, solution = _pair("verified", model_answer="5")
    assert answer_key(problem, solution) == "5"
    assert forbidden_answers(problem, solution) == "5"


def test_low_confidence_hint_cannot_reveal_true_answer() -> None:
    problem, solution = _pair("low_confidence", model_answer="6")
    hint = "Sonuç 5 olur, kontrol etmeyi unutma."

    # Yalnızca modelin (yanlış) cevabı yasak olsaydı gerçek cevap ipucunda geçebilirdi.
    old = check_hint(hint, level=2, final_answer="6", steps=[], problem_text=PROBLEM_TEXT)
    assert old.ok

    new = check_hint(
        hint,
        level=2,
        final_answer=forbidden_answers(problem, solution),
        steps=[],
        problem_text=PROBLEM_TEXT,
    )
    assert not new.ok
