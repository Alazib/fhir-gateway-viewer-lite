from typing import Protocol

from fhir_gateway.domain.entities.condition import Condition
from fhir_gateway.domain.value_objects.resource_id import ResourceId


class ConditionReader(Protocol):
    def list_by_patient(self, patient_id: ResourceId) -> tuple[Condition, ...]: ...
