from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fhir_gateway.infrastructure.persistence.sqlalchemy.base import Base


class PatientRecord(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name_text: Mapped[str | None] = mapped_column(String, nullable=True)
    name_family: Mapped[str | None] = mapped_column(String, nullable=True)
    name_given: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

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
