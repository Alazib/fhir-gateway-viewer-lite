from typing import Protocol

from fhir_gateway.domain.entities.patient import Patient


class PatientSearchReader(Protocol):
    def search_by_text(self, search_text: str) -> tuple[Patient, ...]: ...
