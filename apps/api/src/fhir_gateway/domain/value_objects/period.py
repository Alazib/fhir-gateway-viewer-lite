from dataclasses import dataclass

from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.helpers.type_validator import type_validator
from fhir_gateway.domain.value_objects.instant import Instant


@dataclass(frozen=True, slots=True)
class Period:
    start: Instant | None = None
    end: Instant | None = None

    def __post_init__(self) -> None:
        if self.start is not None:
            type_validator(self, "start", Instant, "must be a Instant")

        if self.end is not None:
            type_validator(self, "end", Instant, "must be a Instant")

        if self.start is not None and self.end is not None:
            if self.start.value > self.end.value:
                raise DomainValidationError("Period", "start must be <= end")
