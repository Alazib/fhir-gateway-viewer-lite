from dataclasses import dataclass
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.helpers.type_validator import type_validator


@dataclass(frozen=True, slots=True)
class ResourceId:
    value: str

    def __post_init__(self) -> None:

        type_validator(self, "value", str)

        cleaned = self.value.strip()
        if cleaned == "":
            raise DomainValidationError("value", "cannot be empty")

        object.__setattr__(self, "value", cleaned)
