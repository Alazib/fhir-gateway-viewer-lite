from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from fhir_gateway.domain.entities.audit_event import AuditAction
from fhir_gateway.domain.value_objects.reference import ALLOWED_REFERENCE_RESOURCE_TYPES
from fhir_gateway.infrastructure.persistence.sqlalchemy.base import Base


AUDIT_ACTION_VALUES = tuple(action.value for action in AuditAction)

AUDIT_ENTITY_RESOURCE_TYPE_VALUES = tuple(
    sorted(ALLOWED_REFERENCE_RESOURCE_TYPES)
)

_AUDIT_ACTION_CHECK_SQL = "action IN (" + ", ".join(
    f"'{action}'" for action in AUDIT_ACTION_VALUES
) + ")"

_AUDIT_ENTITY_RESOURCE_TYPE_CHECK_SQL = (
    "entity_resource_type IN ("
    + ", ".join(
        f"'{resource_type}'"
        for resource_type in AUDIT_ENTITY_RESOURCE_TYPE_VALUES
    )
    + ")"
)


class AuditEventRecord(Base):
    __tablename__ = "audit_events"

    __table_args__ = (
        CheckConstraint(
            _AUDIT_ACTION_CHECK_SQL,
            name="ck_audit_events_action_allowed",
        ),
        CheckConstraint(
            _AUDIT_ENTITY_RESOURCE_TYPE_CHECK_SQL,
            name="ck_audit_events_entity_resource_type_allowed",
        ),
        CheckConstraint(
            "btrim(agent) <> ''",
            name="ck_audit_events_agent_not_empty",
        ),
        Index("ix_audit_events_recorded_at", "recorded_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    agent: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    entity_resource_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_id: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
