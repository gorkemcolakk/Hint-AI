"""FastAPI OpenAPI şemasını dosyaya yazar; istemci tipleri bu dosyadan üretilir.

Kullanım (apps/api içinden): python -m scripts.export_openapi ../client/openapi.json
"""

import json
import sys
from pathlib import Path

from app.main import app


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Kullanım: python -m scripts.export_openapi <çıktı-dosyası>")
    target = Path(sys.argv[1])
    schema = json.dumps(app.openapi(), indent=2, ensure_ascii=False)
    with target.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(schema + "\n")
    print(f"OpenAPI şeması yazıldı: {target}")


if __name__ == "__main__":
    main()
