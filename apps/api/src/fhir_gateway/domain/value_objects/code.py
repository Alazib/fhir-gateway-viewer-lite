from dataclasses import dataclass
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.helpers.type_validator import type_validator


@dataclass(frozen=True, slots=True)
class Code:
    system: str
    code: str
    display: str | None = None

    def __post_init__(self) -> None:

        type_validator(self, "system", str)

        cleaned = self.system.strip()
        if cleaned == "":
            raise DomainValidationError("system", "cannot be empty")

        object.__setattr__(self, "system", cleaned)

        type_validator(self, "code", str)

        cleaned = self.code.strip()
        if cleaned == "":
            raise DomainValidationError("code", "cannot be empty")

        object.__setattr__(self, "code", cleaned)

        if self.display is not None:

            type_validator(self, "display", str)

            cleaned = self.display.strip()
            object.__setattr__(self, "display", cleaned if cleaned != "" else None)
