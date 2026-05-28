from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from fhir_gateway.infrastructure.persistence.sqlalchemy.base import Base
from fhir_gateway.infrastructure.persistence.sqlalchemy.mixins import TimestampMixin


class ConditionCodeRecord(TimestampMixin, Base):
    __tablename__ = "condition_codes"

    __table_args__ = (
        UniqueConstraint(
            "system",
            "code",
            name="uq_condition_codes_system_code",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    system: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)
    display: Mapped[str | None] = mapped_column(String, nullable=True)


class ConditionRecord(TimestampMixin, Base):
    __tablename__ = "conditions"

    __table_args__ = (
        Index("ix_conditions_patient_id", "patient_id"),
        Index("ix_conditions_patient_code", "patient_id", "code_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    code_id: Mapped[int] = mapped_column(
        ForeignKey("condition_codes.id"),
        nullable=False,
    )
    recorded_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
