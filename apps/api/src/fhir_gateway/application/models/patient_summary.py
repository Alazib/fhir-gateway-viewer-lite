from dataclasses import dataclass

from fhir_gateway.application.errors import ApplicationValidationError
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

    def __post_init__(self) -> None:
        if not isinstance(self.patient, Patient):
            raise ApplicationValidationError(
                "PatientSummary.patient",
                "must be a Patient",
            )

        conditions = self._validate_and_normalize_tuple(
            field_name="conditions",
            value=self.conditions,
            expected_type=Condition,
            expected_type_name="Condition",
        )
        object.__setattr__(self, "conditions", conditions)

        encounters = self._validate_and_normalize_tuple(
            field_name="encounters",
            value=self.encounters,
            expected_type=Encounter,
            expected_type_name="Encounter",
        )
        object.__setattr__(self, "encounters", encounters)

        observations = self._validate_and_normalize_tuple(
            field_name="observations",
            value=self.observations,
            expected_type=Observation,
            expected_type_name="Observation",
        )
        object.__setattr__(self, "observations", observations)

    @staticmethod
    def _validate_and_normalize_tuple(
        field_name: str,
        value: object,
        expected_type: type,
        expected_type_name: str,
    ) -> tuple:
        if isinstance(value, str) or not isinstance(value, (list, tuple)):
            raise ApplicationValidationError(
                f"PatientSummary.{field_name}",
                f"must be a list or a tuple of {expected_type_name}",
            )

        if not all(isinstance(item, expected_type) for item in value):
            raise ApplicationValidationError(
                f"PatientSummary.{field_name}",
                f"must contain only {expected_type_name}",
            )

        return tuple(value)
