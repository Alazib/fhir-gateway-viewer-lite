from sqlalchemy import String, UniqueConstraint
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
