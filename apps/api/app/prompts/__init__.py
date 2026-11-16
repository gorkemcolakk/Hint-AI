"""Sürümlü prompt dosyaları. Prompt değişikliği = yeni sürüm dosyası + eval + PR (Kural 7)."""

from functools import cache
from pathlib import Path

from app.modules.llm_gateway.mask import TrustedText

_PROMPT_DIR = Path(__file__).parent


@cache
def load_prompt(name: str) -> TrustedText:
    """`app/prompts/<name>.md` dosyasını uygulamanın güvenilir metni olarak yükler."""
    return TrustedText((_PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8").strip())
