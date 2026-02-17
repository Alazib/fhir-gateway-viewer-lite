from dataclasses import dataclass
from fhir_gateway.domain.helpers.type_validator import type_validator
from fhir_gateway.domain.helpers.normalizer import normalize_string
from fhir_gateway.domain.errors import DomainValidationError


@dataclass(frozen=True, slots=True)
class Quantity:
    value: float | int | None = None
    unit: str | None = None

    def __post_init__(self) -> None:

        if self.value is not None:
            type_validator(self, "value", (float, int), "must be a float or int")

        if self.unit is not None:
            type_validator(self, "unit", str)

            unit_cleaned = normalize_string(self, "unit", False)
            object.__setattr__(self, "unit", unit_cleaned)

        if self.value is not None and self.unit is None:
            raise DomainValidationError(
                "Quantity.unit", "cannot be empty when Quantity.value is present"
            )
