from typing import Protocol

from fhir_gateway.domain.entities.observation import Observation
from fhir_gateway.domain.value_objects.resource_id import ResourceId


class ObservationReader(Protocol):
    def list_by_patient(self, patient_id: ResourceId) -> tuple[Observation, ...]: ...
