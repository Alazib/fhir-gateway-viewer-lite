from dataclasses import dataclass
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.helpers.type_validator import type_validator
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.code import Code
from fhir_gateway.domain.value_objects.instant import Instant


@dataclass(frozen=True, slots=True)
class Condition:
    id: ResourceId
    code: Code
    subject: Reference
    recorded_date: Instant | None = None

    def __post_init__(self) -> None:

        type_validator(self, "id", ResourceId, "must be a ResourceId")

        type_validator(self, "code", Code, "must be a Code")

        type_validator(self, "subject", Reference, "must be a Reference")
        if self.subject.resource_type != "Patient":
            raise DomainValidationError("Condition.subject", "must reference Patient")

        if self.recorded_date is not None:
            type_validator(self, "recorded_date", Instant, "must be an Instant")
