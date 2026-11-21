"""Kural tabanlı sızıntı kontrolü ve demo sağlayıcısı birim testleri (DB gerektirmez)."""

import pytest

from app.modules.llm_gateway.demo import solve_text, write_hint
from app.modules.problems.verify import verify_solution
from app.modules.tutoring import ladder
from app.modules.tutoring.leak import check_hint, turkish_number_words

PROBLEM = "3x + 5 = 20 ise x kaçtır?"
STEPS = ["Her iki taraftan 5 çıkar: 3x = 15", "Her iki tarafı 3'e böl: x = 5"]


def _check(
    hint: str,
    level: int = 2,
    answer: str = "5",
    steps: list[str] | None = None,
    problem: str = PROBLEM,
) -> list[str]:
    result = check_hint(
        hint,
        level=level,
        final_answer=answer,
        steps=STEPS if steps is None else steps,
        problem_text=problem,
    )
    assert result.ok == (not result.reasons)
    return result.reasons


@pytest.mark.parametrize(
    ("hint", "level", "answer", "problem"),
    [
        ("Sonuç 5 olur.", 2, "5", PROBLEM),
        ("x = 5 bulunur", 2, "5", PROBLEM),
        ("Cevap beş!", 1, "5", PROBLEM),
        ("Cevabın 5'tir", 2, "5", PROBLEM),
        ("Sonuç 0,75 çıkıyor", 2, "3/4", "3/4 kaçtır, ondalık yaz"),
        ("Sonuç 3/4", 2, "0.75", "6/8 sadeleştir"),
        ("Cevap yirmi beşe eşit", 2, "25", "5*5"),
        ("x = -7 ya da 7", 2, "7; -7", "x^2 = 49"),
        ("Sonuç 2√3 olur", 2, "2*sqrt(3)", "sqrt(12)"),
        ("Yaklaşık 1,41 çıkar", 2, "sqrt(2)", "x^2 = 2"),
        ("2x + 3 = 11 örneğinde x = 5 bulunur.", 4, "5", PROBLEM),
    ],
)
def test_final_answer_leaks_are_caught(hint: str, level: int, answer: str, problem: str) -> None:
    assert _check(hint, level=level, answer=answer, steps=[], problem=problem)


@pytest.mark.parametrize(
    "hint",
    [
        "Bu denklemde neyi bulmaya çalışıyoruz?",
        "x'i yalnız bırakmak için önce 5'ten kurtulalım.",
        "Eşitliğin iki tarafından aynı sayıyı çıkarabilirsin; 5'i hangi işlemle yok edersin?",
    ],
)
def test_safe_hints_pass_even_when_answer_appears_in_problem(hint: str) -> None:
    assert _check(hint) == []


def test_intermediate_value_forbidden_until_l3() -> None:
    hint = "Sol tarafta 3x = 15 kalır, şimdi sen devam et."
    assert _check(hint, level=2) == ["intermediate:15"]
    assert _check(hint, level=3) == []


def test_l4_example_with_different_answer_passes() -> None:
    assert _check("2x + 3 = 11 örneğinde x = 4 bulunur.", level=4) == []


def test_unparseable_answer_fails_closed() -> None:
    assert _check("Neyi bulmalıyız?", answer="bilinmiyor") == ["final_answer_unparseable"]


def test_turkish_number_words() -> None:
    assert turkish_number_words(5) == "beş"
    assert turkish_number_words(40) == "kırk"
    assert turkish_number_words(125) == "yüz yirmi beş"
    assert turkish_number_words(300) == "üç yüz"


def test_ladder_levels_and_caps() -> None:
    assert ladder.next_level(None, status="verified", frustrated=False) == 0
    assert ladder.next_level(None, status="verified", frustrated=True) == 1
    assert ladder.next_level(3, status="verified", frustrated=False) == 4
    assert ladder.next_level(4, status="verified", frustrated=False) == 4
    assert ladder.next_level(1, status="low_confidence", frustrated=False) == 2
    assert ladder.next_level(2, status="unverifiable", frustrated=False) == 2
    assert ladder.next_level(1, status="failed", frustrated=False) == 1
    assert ladder.is_frustrated("bu çok zor, yapamıyorum")
    assert not ladder.is_frustrated("x'i buldum sanırım")


@pytest.mark.parametrize(
    "fallback", [text for hints in ladder.FALLBACK_HINTS.values() for text in hints.values()]
)
def test_fallback_hints_contain_no_numbers(fallback: str) -> None:
    assert not any(ch.isdigit() for ch in fallback)


@pytest.mark.parametrize(
    ("text", "answer"),
    [
        ("3x + 5 = 20 ise x kaçtır?", "5"),
        ("2x - 4 = 10", "7"),
        ("12 : 4 + 3 × 2 kaçtır?", "9"),
        ("3/4 + 1/8 işleminin sonucu nedir?", "7/8"),
    ],
)
def test_demo_solver_solves_and_verifies(text: str, answer: str) -> None:
    solved = solve_text(text)
    assert solved is not None
    assert solved["final_answer"] == answer
    assert verify_solution(solved["sympy_check"], solved["final_answer"]).status == "verified"


def test_demo_solver_gives_up_on_word_problems() -> None:
    assert solve_text("Ali'nin elmalarının yarısını yedi, kaç tane kaldı?") is None


@pytest.mark.parametrize("level", [0, 1, 2, 3, 4])
def test_demo_hints_respect_leak_rules(level: int) -> None:
    solved = solve_text(PROBLEM)
    assert solved is not None
    request = ladder.build_hint_request(
        problem_text=PROBLEM,
        steps=solved["steps"],
        final_answer=solved["final_answer"],
        level=level,
        age_band="11-13",
        previous_hints=[],
        student_message=None,
        frustrated=False,
    )
    # L4'te demo farklı örnekler arasında döner; en az biri sızıntısız olmalı.
    results = [
        check_hint(
            write_hint(request, variant),
            level=level,
            final_answer=solved["final_answer"],
            steps=solved["steps"],
            problem_text=PROBLEM,
        ).ok
        for variant in range(3)
    ]
    assert any(results)


@pytest.mark.parametrize(
    ("text", "check", "kind"),
    [
        ("3x + 5 = 20 ise x kaçtır?", {"type": "solve"}, "equation"),
        ("3/4 + 1/8 kaç eder?", {"type": "evaluate"}, "arithmetic"),
        ("2/3 ile 3/5'i çarpınca ne bulunur?", {"type": "evaluate"}, "arithmetic"),
        ("Ayşe'nin 12 elması var, yarısını kardeşine verdi. Kaç elması kaldı?", None, "word"),
    ],
)
def test_problem_kind(text: str, check: dict[str, str] | None, kind: str) -> None:
    assert ladder.problem_kind(text, check) == kind


def test_fallback_hint_matches_problem_kind() -> None:
    assert "denklem" in ladder.fallback_hint(1, topic=None, support=False, kind="equation")
    assert "İşlem önceliği" in ladder.fallback_hint(1, topic=None, support=False, kind="arithmetic")
