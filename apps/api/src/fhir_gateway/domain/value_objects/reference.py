from dataclasses import dataclass

from fhir_gateway.domain.helpers.normalizer import normalize_string
from fhir_gateway.domain.helpers.type_validator import type_validator
from fhir_gateway.domain.value_objects.resource_id import ResourceId


@dataclass(frozen=True, slots=True)
class Reference:
    resource_type: str
    id: ResourceId

    def __post_init__(self) -> None:

        type_validator(self, "resource_type", str)

        resource_type_cleaned = normalize_string(self, "resource_type")
        object.__setattr__(self, "resource_type", resource_type_cleaned)

        type_validator(self, "id", ResourceId, "must be a ResourceId")
