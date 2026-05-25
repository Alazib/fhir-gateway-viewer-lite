"""create patient tables

Revision ID: f97f9d019499
Revises:
Create Date: 2026-05-25 17:33:08.020264

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f97f9d019499'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name_text", sa.String(), nullable=True),
        sa.Column("name_family", sa.String(), nullable=True),
        sa.Column("name_given", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "patient_identifiers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.String(), nullable=False),
        sa.Column("system", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "patient_id",
            "system",
            "value",
            name="uq_patient_identifiers_patient_system_value",
        ),
    )

    op.create_index(
        "ix_patient_identifiers_system_value",
        "patient_identifiers",
        ["system", "value"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_patient_identifiers_system_value",
        table_name="patient_identifiers",
    )
    op.drop_table("patient_identifiers")
    op.drop_table("patients")
