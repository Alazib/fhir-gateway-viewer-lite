from dataclasses import dataclass
from fhir_gateway.domain.errors import DomainValidationError


@dataclass(frozen=True, slots=True)
class Code:
    system: str
    code: str
    display: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.system, str):
            raise DomainValidationError("system", "must be a string")

        cleaned = self.system.strip()
        if cleaned == "":
            raise DomainValidationError("system", "cannot be empty")

        object.__setattr__(self, "system", cleaned)

        if not isinstance(self.code, str):
            raise DomainValidationError("code", "must be a string")

        cleaned = self.code.strip()
        if cleaned == "":
            raise DomainValidationError("code", "cannot be empty")

        object.__setattr__(self, "code", cleaned)

        if self.display is not None:

            if not isinstance(self.display, str):
                raise DomainValidationError("display", "must be a string")

            cleaned = self.display.strip()
            if cleaned == "":
                object.__setattr__(self, "display", None)
            else:
                object.__setattr__(self, "display", cleaned)
