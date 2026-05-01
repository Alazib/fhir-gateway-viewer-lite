from typing import Protocol

from fhir_gateway.domain.entities.observation import Observation
from fhir_gateway.domain.value_objects.code import Code
from fhir_gateway.domain.value_objects.resource_id import ResourceId


class ObservationByCodeReader(Protocol):
    def list_by_patient_and_code(
        self,
        patient_id: ResourceId,
        code: Code,
    ) -> tuple[Observation, ...]: ...
