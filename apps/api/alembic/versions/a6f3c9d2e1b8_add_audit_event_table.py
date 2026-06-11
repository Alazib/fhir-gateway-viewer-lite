"""add audit event table

Revision ID: a6f3c9d2e1b8
Revises: d4e8f2a1c9b7
Create Date: 2026-06-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a6f3c9d2e1b8"
down_revision: Union[str, Sequence[str], None] = "d4e8f2a1c9b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


AUDIT_ACTION_VALUES = (
    "read",
    "search",
    "export",
)

AUDIT_ENTITY_RESOURCE_TYPE_VALUES = (
    "Condition",
    "Encounter",
    "Observation",
    "Patient",
)

AUDIT_ACTION_CHECK_SQL = "action IN (" + ", ".join(
    f"'{action}'" for action in AUDIT_ACTION_VALUES
) + ")"

AUDIT_ENTITY_RESOURCE_TYPE_CHECK_SQL = (
    "entity_resource_type IN ("
    + ", ".join(
        f"'{resource_type}'"
        for resource_type in AUDIT_ENTITY_RESOURCE_TYPE_VALUES
    )
    + ")"
)


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("agent", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("entity_resource_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            AUDIT_ACTION_CHECK_SQL,
            name="ck_audit_events_action_allowed",
        ),
        sa.CheckConstraint(
            AUDIT_ENTITY_RESOURCE_TYPE_CHECK_SQL,
            name="ck_audit_events_entity_resource_type_allowed",
        ),
        sa.CheckConstraint(
            "btrim(agent) <> ''",
            name="ck_audit_events_agent_not_empty",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audit_events_recorded_at",
        "audit_events",
        ["recorded_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_audit_events_recorded_at",
        table_name="audit_events",
    )
    op.drop_table("audit_events")
