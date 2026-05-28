from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from fhir_gateway.domain.entities.observation import ObservationStatus
from fhir_gateway.infrastructure.persistence.sqlalchemy.base import Base
from fhir_gateway.infrastructure.persistence.sqlalchemy.mixins import TimestampMixin


OBSERVATION_STATUS_VALUES = tuple(status.value for status in ObservationStatus)

_OBSERVATION_STATUS_CHECK_SQL = "status IN (" + ", ".join(
    f"'{status}'" for status in OBSERVATION_STATUS_VALUES
) + ")"


class ObservationCodeRecord(TimestampMixin, Base):
    __tablename__ = "observation_codes"

    __table_args__ = (
        UniqueConstraint(
            "system",
            "code",
            name="uq_observation_codes_system_code",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    system: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)
    display: Mapped[str | None] = mapped_column(String, nullable=True)


class ObservationRecord(TimestampMixin, Base):
    __tablename__ = "observations"

    __table_args__ = (
        CheckConstraint(
            _OBSERVATION_STATUS_CHECK_SQL,
            name="ck_observations_status_allowed",
        ),
        CheckConstraint(
            "value_quantity IS NULL OR value_unit IS NOT NULL",
            name="ck_observations_value_quantity_requires_unit",
        ),
        Index("ix_observations_patient_code", "patient_id", "code_id"),
        Index(
            "ix_observations_patient_effective_at",
            "patient_id",
            "effective_at",
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    code_id: Mapped[int] = mapped_column(
        ForeignKey("observation_codes.id"),
        nullable=False,
    )
    effective_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    value_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_unit: Mapped[str | None] = mapped_column(String, nullable=True)
