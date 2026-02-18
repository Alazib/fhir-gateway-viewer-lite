from dataclasses import dataclass

from fhir_gateway.domain.helpers.type_validator import type_validator
from fhir_gateway.domain.value_objects.human_name import HumanName
from fhir_gateway.domain.value_objects.identifier import Identifier
from fhir_gateway.domain.value_objects.resource_id import ResourceId


@dataclass(frozen=True, slots=True)
class Patient:
    id: ResourceId
    identifier: Identifier | None = None
    name: HumanName | None = None

    def __post_init__(self) -> None:

        type_validator(self, "id", ResourceId, "must be a ResourceId")

        if self.identifier is not None:
            type_validator(self, "identifier", Identifier, "must be an Identifier")

        if self.name is not None:
            type_validator(self, "name", HumanName, "must be a HumanName")
