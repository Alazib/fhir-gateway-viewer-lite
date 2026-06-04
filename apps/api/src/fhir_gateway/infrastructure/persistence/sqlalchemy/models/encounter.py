from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from fhir_gateway.infrastructure.persistence.sqlalchemy.base import Base
from fhir_gateway.infrastructure.persistence.sqlalchemy.mixins import (
    LogicalDeletionMixin,
    TimestampMixin,
)


class EncounterRecord(LogicalDeletionMixin, TimestampMixin, Base):
    __tablename__ = "encounters"

    __table_args__ = (
        CheckConstraint(
            "period_end_at IS NULL OR period_start_at <= period_end_at",
            name="ck_encounters_period_start_before_end",
        ),
        Index(
            "ix_encounters_patient_period_start_at",
            "patient_id",
            "period_start_at",
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    period_start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    period_end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
