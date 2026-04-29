from dataclasses import dataclass
from fhir_gateway.domain.entities.condition import Condition
from fhir_gateway.domain.entities.encounter import Encounter
from fhir_gateway.domain.entities.observation import Observation
from fhir_gateway.domain.entities.patient import Patient


@dataclass(frozen=True, slots=True)
class PatientSummary:
    patient: Patient
    conditions: tuple[Condition, ...]
    encounters: tuple[Encounter, ...]
    observations: tuple[Observation, ...]
