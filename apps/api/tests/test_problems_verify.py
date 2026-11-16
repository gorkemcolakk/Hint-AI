"""SymPy doğrulayıcısı ve çözüm ayrıştırma birim testleri."""

import pytest

from app.modules.problems.service import parse_solution
from app.modules.problems.verify import (
    UnsafeExpressionError,
    answers_match,
    parse_math,
    verify_solution,
)
from evals.run_solution_eval import run_solution_eval


def test_verifies_equation_and_expression_answers() -> None:
    solve = {"type": "solve", "equation": "3*x + 5 = 20", "variable": "x"}
    assert verify_solution(solve, "x = 5").status == "verified"
    assert verify_solution(solve, "5").status == "verified"
    assert verify_solution({"type": "evaluate", "expression": "3/4 + 1/8"}, "0.875").status == (
        "verified"
    )
    roots = {"type": "solve", "equation": "x^2 = 49", "variable": "x"}
    assert verify_solution(roots, "7; -7").status == "verified"
    assert (
        verify_solution(
            {"type": "evaluate", "expression": "sqrt(50) + sqrt(18)"}, "8*sqrt(2)"
        ).status
        == "verified"
    )


def test_wrong_answer_is_mismatch() -> None:
    result = verify_solution({"type": "solve", "equation": "3*x + 5 = 20", "variable": "x"}, "6")
    assert result.status == "mismatch"


def test_missing_or_unknown_check_is_unverifiable() -> None:
    assert verify_solution(None, "7").status == "unverifiable"
    assert verify_solution({"type": "integrate"}, "7").status == "unverifiable"
    assert verify_solution({"type": "solve", "equation": "x > 6", "variable": "x"}, "7").status == (
        "unverifiable"
    )


@pytest.mark.parametrize(
    "expression",
    [
        '__import__("os").system("calc")',
        "open(1)",
        "eval(1)",
        "lambda: 1",
        "9^99999",
        "2^3^4",
        "1" * 20,
        "x" * 300,
    ],
)
def test_unsafe_expressions_are_rejected_before_parsing(expression: str) -> None:
    # SymPy ayrıştırıcısı eval kullanır; LLM çıktısı kod çalıştıramamalı, işlemciyi kilitleyememeli.
    with pytest.raises(UnsafeExpressionError):
        parse_math(expression)


def test_single_letters_are_plain_symbols() -> None:
    # E, I, N, S SymPy'da özel nesnelerdir; kullanıcı ifadesinde değişken olarak kalmalı.
    assert str(parse_math("2*E + I")) == "2*E + I"


def test_answers_match_ignores_format_and_order() -> None:
    assert answers_match("7; -7", "x = -7; x = 7")
    assert answers_match("0.6", "3/5")
    assert not answers_match("7; -7", "7")
    assert not answers_match("5", "cevap beş")


def test_parse_solution_tolerates_code_fences() -> None:
    content = '```json\n{"final_answer": "5", "steps": ["a"], "sympy_check": null}\n```'
    payload = parse_solution(content)
    assert payload is not None and payload.final_answer == "5"
    assert parse_solution("JSON vermiyorum") is None
    assert parse_solution('{"steps": []}') is None


@pytest.mark.asyncio
async def test_golden_set_reference_answers_are_consistent() -> None:
    report = await run_solution_eval(real=False)
    assert report["passed"] is True
    assert report["total_cases"] >= 60
    assert report["accuracy_percent"] == 100.0
