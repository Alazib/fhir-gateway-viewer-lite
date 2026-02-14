from dataclasses import dataclass
from fhir_gateway.domain.helpers.normalizer import normalize_string
from fhir_gateway.domain.helpers.type_validator import type_validator


@dataclass(frozen=True, slots=True)
class Code:
    system: str
    code: str
    display: str | None = None

    def __post_init__(self) -> None:

        type_validator(self, "system", str)

        cleaned_system = normalize_string(self, "system")

        object.__setattr__(self, "system", cleaned_system)

        type_validator(self, "code", str)

        cleaned_code = normalize_string(self, "code")

        object.__setattr__(self, "code", cleaned_code)

        if self.display is not None:

            type_validator(self, "display", str)

            cleaned_display = normalize_string(self, "display", False)

            object.__setattr__(self, "display", cleaned_display)
