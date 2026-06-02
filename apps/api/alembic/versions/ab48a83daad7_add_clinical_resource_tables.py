"""add clinical resource tables

Revision ID: ab48a83daad7
Revises: f97f9d019499
Create Date: 2026-06-02 15:23:45.731724

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab48a83daad7'
down_revision: Union[str, Sequence[str], None] = 'f97f9d019499'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OBSERVATION_STATUS_VALUES = (
    "registered",
    "preliminary",
    "final",
    "amended",
    "corrected",
    "cancelled",
    "entered-in-error",
    "unknown",
)

OBSERVATION_STATUS_CHECK_SQL = "status IN (" + ", ".join(
    f"'{status}'" for status in OBSERVATION_STATUS_VALUES
) + ")"


def upgrade() -> None:
    op.create_table(
        "observation_codes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("system", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("display", sa.String(), nullable=True),
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
        sa.UniqueConstraint(
            "system",
            "code",
            name="uq_observation_codes_system_code",
        ),
    )

    op.create_table(
        "condition_codes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("system", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("display", sa.String(), nullable=True),
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
        sa.UniqueConstraint(
            "system",
            "code",
            name="uq_condition_codes_system_code",
        ),
    )

    op.create_table(
        "observations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("patient_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("code_id", sa.Integer(), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value_quantity", sa.Float(), nullable=True),
        sa.Column("value_unit", sa.String(), nullable=True),
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
        sa.CheckConstraint(
            OBSERVATION_STATUS_CHECK_SQL,
            name="ck_observations_status_allowed",
        ),
        sa.CheckConstraint(
            "value_quantity IS NULL OR value_unit IS NOT NULL",
            name="ck_observations_value_quantity_requires_unit",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["code_id"],
            ["observation_codes.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_observations_patient_code",
        "observations",
        ["patient_id", "code_id"],
        unique=False,
    )
    op.create_index(
        "ix_observations_patient_effective_at",
        "observations",
        ["patient_id", "effective_at"],
        unique=False,
    )

    op.create_table(
        "conditions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("patient_id", sa.String(), nullable=False),
        sa.Column("code_id", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["code_id"],
            ["condition_codes.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_conditions_patient_code",
        "conditions",
        ["patient_id", "code_id"],
        unique=False,
    )

    op.create_table(
        "encounters",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("patient_id", sa.String(), nullable=False),
        sa.Column("period_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint(
            "period_end_at IS NULL OR period_start_at <= period_end_at",
            name="ck_encounters_period_start_before_end",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_encounters_patient_period_start_at",
        "encounters",
        ["patient_id", "period_start_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_encounters_patient_period_start_at",
        table_name="encounters",
    )
    op.drop_table("encounters")

    op.drop_index(
        "ix_conditions_patient_code",
        table_name="conditions",
    )
    op.drop_table("conditions")

    op.drop_index(
        "ix_observations_patient_effective_at",
        table_name="observations",
    )
    op.drop_index(
        "ix_observations_patient_code",
        table_name="observations",
    )
    op.drop_table("observations")

    op.drop_table("condition_codes")
    op.drop_table("observation_codes")
