"""Yerel demo verisi: ebeveyn + rızaları verilmiş çocuk + eşleştirme bağlantısı.

Tekrar çalıştırılabilir; ebeveyn ve çocuk varsa yeniden kullanılır, her seferinde yeni bir
eşleştirme kodu (10 dk geçerli) üretilir. Yalnızca sahte veri, yalnızca yerel geliştirme.
HINT_DEV_SHORTCUTS=true iken giriş ekranındaki demo düğmeleri bu adıma gerek bırakmaz.

    cd apps/api
    .venv\\Scripts\\python -m scripts.seed_demo
"""

import asyncio

from app.core.config import settings
from app.core.db import _session_factory, engine
from app.modules.auth_consent.service import create_pairing_code
from app.modules.dev.demo import (
    DEMO_CHILD_GRADE,
    DEMO_CHILD_NICKNAME,
    DEMO_EMAIL,
    DEMO_PASSWORD,
    ensure_demo_family,
)

CLIENT_URL = "http://localhost:8081"


async def main() -> None:
    if settings.environment != "local":
        raise SystemExit("Demo verisi yalnızca HINT_ENVIRONMENT=local iken oluşturulur.")
    async with _session_factory() as db:
        guardian, child = await ensure_demo_family(db)
        pairing = await create_pairing_code(db, guardian, child.id)
    await engine.dispose()

    print("Demo verisi hazır (sahte veri).")
    print(f"  Ebeveyn girişi : {DEMO_EMAIL} / {DEMO_PASSWORD}")
    print(f"  Çocuk          : {DEMO_CHILD_NICKNAME}, {DEMO_CHILD_GRADE}. sınıf")
    print(f"  Çocuk modu     : {CLIENT_URL}/pair?child={child.id}&code={pairing.code}")
    print("                   (bağlantı 10 dk geçerli, tek kullanımlık)")


if __name__ == "__main__":
    asyncio.run(main())
