from dataclasses import dataclass

from fhir_gateway.domain.errors import DomainValidationError


@dataclass(frozen=True, slots=True)
class ResourceId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise DomainValidationError("ResourceId", "must be a string")

        cleaned = self.value.strip()
        if cleaned == "":
            raise DomainValidationError("ResourceId", "cannot be empty")

        object.__setattr__(self, "value", cleaned)
