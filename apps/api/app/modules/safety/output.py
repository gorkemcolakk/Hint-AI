"""Çıktı güvenliği (Hint Engine adım 8): modelin yazdığı metin çocuğa gitmeden kontrol edilir."""

import re

from app.modules.llm_gateway.mask import mask_pii
from app.modules.safety.classifier import classify

_LINK = re.compile(r"https?://|www\.|\b[\w-]+\.(?:com|net|org|io|tr)\b", re.IGNORECASE)
_UNSAFE_OUTPUT = {"self_harm", "abuse_disclosure", "sexual_content", "violence"}


def check_output(text: str) -> list[str]:
    """Sorun yoksa boş liste; varsa neden kodları (metin içermez)."""
    reasons: list[str] = []
    detected = mask_pii(text).detected_types
    if detected:
        reasons.append("output_pii:" + ",".join(sorted(detected)))
    if _LINK.search(text):
        reasons.append("output_link")
    verdict = classify(text)
    if verdict.category in _UNSAFE_OUTPUT:
        reasons.append(f"output_unsafe:{verdict.category}")
    return reasons
