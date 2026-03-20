from dataclasses import dataclass

from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.helpers.type_validator import type_validator
from fhir_gateway.domain.value_objects.human_name import HumanName
from fhir_gateway.domain.value_objects.identifier import Identifier
from fhir_gateway.domain.value_objects.resource_id import ResourceId


@dataclass(frozen=True, slots=True)
class Patient:

    id: ResourceId
    identifiers: tuple[Identifier, ...] = ()
    name: HumanName | None = None

    def __post_init__(self) -> None:

        type_validator(self, "id", ResourceId, "must be a ResourceId")

        if self.name is not None:
            type_validator(self, "name", HumanName, "must be a HumanName")

        identifiers = self.identifiers
        if isinstance(identifiers, list):
            identifiers = tuple(identifiers)
        elif not isinstance(identifiers, tuple):
            raise DomainValidationError(
                "Patient.identifiers", "must be a list or a tuple of Identifier"
            )

        if not all(isinstance(i, Identifier) for i in identifiers):
            raise DomainValidationError(
                "Patient.identifiers", "must be a list/tuple of Identifier"
            )

        # Prevent duplicates (same system + value)
        seen: set[tuple[str, str]] = set()
        for i in identifiers:
            key = (i.system, i.value)
            if key in seen:
                raise DomainValidationError(
                    "Patient.identifiers", "duplicate Identifier (system, value)"
                )
            seen.add(key)

        object.__setattr__(self, "identifiers", identifiers)
