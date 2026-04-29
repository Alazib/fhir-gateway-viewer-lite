from typing import Protocol

from fhir_gateway.domain.entities.patient import Patient
from fhir_gateway.domain.value_objects.resource_id import ResourceId


class PatientReader(Protocol):
    def get_by_id(self, patient_id: ResourceId) -> Patient | None: ...
