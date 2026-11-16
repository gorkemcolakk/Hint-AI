"""M2.1: pairing_codes.code_hash üzerindeki UNIQUE kısıtı kaldırılır

6 haneli kod uzayında eski kodlarla çakışma IntegrityError (500) üretiyordu.
Kod her zaman child_id ile birlikte arandığı için benzersizlik gerekmez;
ix_pairing_codes_code_hash indeksi korunur.

Revision ID: 20261116_0004
Revises: 20261017_0003
Create Date: 2026-11-16

"""

from alembic import op

revision = "20261116_0004"
down_revision = "20261017_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_pairing_codes_code_hash", "pairing_codes", type_="unique")


def downgrade() -> None:
    # Tabloda aynı hash'e sahip kodlar oluştuysa geri alma başarısız olur; önce bunlar silinmeli.
    op.create_unique_constraint("uq_pairing_codes_code_hash", "pairing_codes", ["code_hash"])
