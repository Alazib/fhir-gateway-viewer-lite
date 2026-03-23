from dataclasses import dataclass
from enum import Enum
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.helpers.type_validator import type_validator
from fhir_gateway.domain.value_objects.code import Code
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.quantity import Quantity
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId


class ObservationStatus(str, Enum):
    REGISTERED = "registered"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Observation:
    id: ResourceId
    status: ObservationStatus
    code: Code
    subject: Reference
    effective: Instant
    value: Quantity

    def __post_init__(self) -> None:

        type_validator(self, "id", ResourceId, "must be a ResourceId")

        type_validator(
            self,
            "status",
            ObservationStatus,
            "must be an ObservationStatus",
        )

        type_validator(self, "code", Code, "must be a Code")

        type_validator(self, "subject", Reference, "must be a Reference")
        if self.subject.resource_type != "Patient":
            raise DomainValidationError("Observation.subject", "must reference Patient")

        type_validator(self, "effective", Instant, "must be an Instant")

        type_validator(self, "value", Quantity, "must be a Quantity")
