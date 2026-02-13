from dataclasses import dataclass
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.helpers.type_validator import type_validator


@dataclass(frozen=True, slots=True)
class Identifier:
    system: str
    value: str

    def __post_init__(self) -> None:

        type_validator(self, "system", str)

        cleaned = self.system.strip()
        if cleaned == "":
            raise DomainValidationError("system", "cannot be empty")

        object.__setattr__(self, "system", cleaned)

        type_validator(self, "value", str)

        cleaned = self.value.strip()
        if cleaned == "":
            raise DomainValidationError("value", "cannot be empty")

        object.__setattr__(self, "value", cleaned)
