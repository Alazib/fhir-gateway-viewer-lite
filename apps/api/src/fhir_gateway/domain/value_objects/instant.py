from dataclasses import dataclass
from datetime import datetime, timezone
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.helpers.type_validator import type_validator


@dataclass(frozen=True, slots=True)
class Instant:
    value: datetime

    def __post_init__(self) -> None:

        type_validator(self, "value", datetime)

        dt = self.value

        # Reject naive datetimes (must be timezone-aware):
        #    - tzinfo is None => naive
        #    - utcoffset() is None => also effectively naive/invalid tz
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise DomainValidationError("Instant.value", "must be timezone-aware")

        # Normalize to UTC so the whole system is consistent:
        dt_utc = dt.astimezone(timezone.utc)
        object.__setattr__(self, "value", dt_utc)
