"""Önceden yazılmış sabit güvenlik metinleri (model üretmez).

⚠️ DOĞRULA: Bu metinler taslaktır. Gerçek çocuklarla kullanımdan önce bir psikolog/pedagog
tarafından onaylanmalı; yardım hatları ve numaraları güncelliği açısından doğrulanmalıdır
(Bölüm 10.2, 21.C).
"""

from dataclasses import dataclass

from app.modules.safety.classifier import Category


@dataclass(frozen=True)
class SupportResource:
    name: str
    phone: str
    note: str


EMERGENCY = SupportResource("Acil Çağrı", "112", "Kendini ya da başkasını tehlikede hissedersen.")
SOCIAL_SUPPORT = SupportResource(
    "ALO 183 Sosyal Destek Hattı", "183", "Çocuklar için ücretsiz destek ve danışma hattı."
)

_SUPPORT: dict[Category, tuple[str, tuple[SupportResource, ...]]] = {
    "self_harm": (
        "Bunu benimle paylaştığın için teşekkür ederim. Şu an zor bir şey yaşıyor gibisin ve "
        "bu çok önemli. Lütfen hemen güvendiğin bir yetişkinle konuş: annen, baban, bir "
        "öğretmenin ya da okul rehber öğretmenin. Kendini tehlikede hissediyorsan 112'yi ara.",
        (EMERGENCY, SOCIAL_SUPPORT),
    ),
    "abuse_disclosure": (
        "Bunu anlattığın için çok cesursun. Kimsenin sana zarar vermeye hakkı yok ve bu senin "
        "suçun değil. Lütfen güvendiğin bir yetişkine anlat. Ücretsiz olarak 183'ü, acil bir "
        "durumdaysan 112'yi arayabilirsin.",
        (EMERGENCY, SOCIAL_SUPPORT),
    ),
    "violence": (
        "Bu konuda sana yardım edemem. Çok kızgın ya da üzgün hissediyorsan güvendiğin bir "
        "yetişkinle konuşmak iyi gelebilir. Biri tehlikedeyse 112'yi ara.",
        (EMERGENCY,),
    ),
    "bullying": (
        "Böyle bir şey yaşıyorsan bu gerçekten üzücü ve senin suçun değil. Bir öğretmenine ya "
        "da ailene anlatman çok önemli. Ben sana matematik sorularında yardım edebilirim.",
        (SOCIAL_SUPPORT,),
    ),
    "sexual_content": (
        "Bu konuda konuşamam. Matematik sorunla ilgili sana yardım etmekten mutluluk duyarım.",
        (),
    ),
}

INJECTION_NOTICE = (
    "Cevabı doğrudan söyleyemem; ama adım adım ipuçlarıyla kendin bulmana yardım edeceğim."
)
PII_NOTICE = "Adını, okulunu ya da telefonunu yazmana gerek yok; bu bilgileri senin için gizledim."


def support_for(category: Category) -> tuple[str, tuple[SupportResource, ...]]:
    return _SUPPORT.get(category, _SUPPORT["sexual_content"])
