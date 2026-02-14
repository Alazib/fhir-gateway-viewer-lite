from dataclasses import dataclass
from fhir_gateway.domain.helpers.normalizer import normalize_string
from fhir_gateway.domain.helpers.type_validator import type_validator


@dataclass(frozen=True, slots=True)
class ResourceId:
    value: str

    def __post_init__(self) -> None:

        type_validator(self, "value", str)

        cleaned_value = normalize_string(self, "value")
        object.__setattr__(self, "value", cleaned_value)
