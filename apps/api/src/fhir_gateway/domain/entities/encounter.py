from dataclasses import dataclass

from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.helpers.type_validator import type_validator
from fhir_gateway.domain.value_objects.period import Period
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId


@dataclass(frozen=True, slots=True)
class Encounter:
    id: ResourceId
    subject: Reference
    period: Period

    def __post_init__(self) -> None:
        type_validator(self, "id", ResourceId, "must be a ResourceId")

        type_validator(self, "subject", Reference, "must be a Reference")
        if self.subject.resource_type != "Patient":
            raise DomainValidationError("Encounter.subject", "must reference Patient")

        type_validator(self, "period", Period, "must be a Period")
        if self.period.start is None:
            raise DomainValidationError("Encounter.period", "start must be present")
