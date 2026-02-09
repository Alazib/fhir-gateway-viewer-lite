from dataclasses import dataclass
from fhir_gateway.domain.errors import DomainValidationError


@dataclass(frozen=True, slots=True)
class Identifier:
    system: str
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.system, str):
            raise DomainValidationError("system", "must be a string")

        cleaned = self.system.strip()
        if cleaned == "":
            raise DomainValidationError("system", "cannot be empty")

        object.__setattr__(self, "system", cleaned)

        if not isinstance(self.value, str):
            raise DomainValidationError("value", "must be a string")

        cleaned = self.value.strip()
        if cleaned == "":
            raise DomainValidationError("value", "cannot be empty")

        object.__setattr__(self, "value", cleaned)
