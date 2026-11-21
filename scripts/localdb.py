"""Docker'sız yerel PostgreSQL (yalnızca geliştirme).

PostgreSQL 16, `pixeltable-pgserver` pip paketinin içinden gelir; sisteme kurulum veya
yönetici izni gerekmez. Veri `<repo>/.local/pgdata` altında durur, sunucu yalnızca
127.0.0.1'i dinler ve parola istemez (trust). Gerçek veriyle KULLANMAYIN.

Kullanım (apps/api/.venv içindeki Python ile):
    python scripts/localdb.py start    # gerekirse oluşturur, başlatır, hint + hint_test DB
    python scripts/localdb.py stop
    python scripts/localdb.py status
"""

import os
import subprocess
import sys
from pathlib import Path

import pixeltable_pgserver

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / ".local" / "pgdata"
LOG = REPO / ".local" / "postgres.log"
BIN = Path(pixeltable_pgserver.__file__).parent / "pginstall" / "bin"
HOST = "127.0.0.1"
PORT = os.environ.get("HINT_LOCAL_PG_PORT", "5432")
USER, DATABASES = "hint", ("hint", "hint_test")


def _exe(name: str) -> str:
    return str(BIN / f"{name}.exe" if os.name == "nt" else BIN / name)


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, capture_output=True, text=True)


def _sql(query: str) -> str:
    result = _run(
        _exe("psql"), "-h", HOST, "-p", PORT, "-U", "postgres", "-d", "postgres", "-tAc", query
    )
    return result.stdout.strip()


def is_running() -> bool:
    args = (_exe("pg_isready"), "-h", HOST, "-p", PORT, "-U", "postgres", "-d", "postgres")
    return _run(*args, check=False).returncode == 0


def start() -> None:
    if not (DATA / "PG_VERSION").exists():
        DATA.parent.mkdir(parents=True, exist_ok=True)
        print(f"Veritabanı klasörü oluşturuluyor: {DATA}")
        _run(
            _exe("initdb"),
            "-D",
            str(DATA),
            "-U",
            "postgres",
            "-A",
            "trust",
            "-E",
            "UTF8",
            "--locale=C",
        )
    if not is_running():
        # Çıktı yakalanmaz: Windows'ta postgres süreci boruyu devralır ve run() hiç dönmez.
        subprocess.run(
            [
                _exe("pg_ctl"),
                "-D",
                str(DATA),
                "-l",
                str(LOG),
                "-w",
                "-o",
                f"-h {HOST} -p {PORT}",
                "start",
            ],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    if _sql(f"SELECT 1 FROM pg_roles WHERE rolname = '{USER}'") != "1":
        _sql(f"CREATE ROLE {USER} LOGIN CREATEDB PASSWORD '{USER}'")
    for name in DATABASES:
        if _sql(f"SELECT 1 FROM pg_database WHERE datname = '{name}'") != "1":
            _sql(f'CREATE DATABASE "{name}" OWNER {USER}')
    print(f"PostgreSQL hazır: postgresql://{USER}:{USER}@{HOST}:{PORT}/hint (+ hint_test)")


def stop() -> None:
    if is_running():
        _run(_exe("pg_ctl"), "-D", str(DATA), "-m", "fast", "stop")
    print("PostgreSQL durduruldu.")


def status() -> None:
    print(f"PostgreSQL {'çalışıyor' if is_running() else 'kapalı'} ({HOST}:{PORT}, {DATA})")


if __name__ == "__main__":
    commands = {"start": start, "stop": stop, "status": status}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        sys.exit(f"Kullanım: python {Path(__file__).name} start|stop|status")
    try:
        commands[sys.argv[1]]()
    except subprocess.CalledProcessError as exc:
        sys.exit(f"Komut başarısız: {' '.join(exc.cmd)}\n{exc.stderr or exc.stdout}\nLog: {LOG}")
