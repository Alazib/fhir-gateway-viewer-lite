from __future__ import annotations

from sqlalchemy import ForeignKey, Index, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fhir_gateway.infrastructure.persistence.sqlalchemy.base import Base
from fhir_gateway.infrastructure.persistence.sqlalchemy.mixins import (
    LogicalDeletionMixin,
    TimestampMixin,
)


class PatientRecord(LogicalDeletionMixin, TimestampMixin, Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name_text: Mapped[str | None] = mapped_column(String, nullable=True)
    name_family: Mapped[str | None] = mapped_column(String, nullable=True)
    name_given: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    identifiers: Mapped[list[PatientIdentifierRecord]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )


class PatientIdentifierRecord(Base):
    __tablename__ = "patient_identifiers"

    __table_args__ = (
        UniqueConstraint(
            "patient_id",
            "system",
            "value",
            name="uq_patient_identifiers_patient_system_value",
        ),
        Index(
            "ix_patient_identifiers_system_value",
            "system",
            "value",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    system: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)

    patient: Mapped[PatientRecord] = relationship(back_populates="identifiers")
