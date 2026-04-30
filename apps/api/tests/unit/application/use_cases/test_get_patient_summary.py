from datetime import datetime, timezone

import pytest

from fhir_gateway.application.errors import (
    ApplicationNotFoundError,
    ApplicationValidationError,
)
from fhir_gateway.application.use_cases.get_patient_summary import (
    GetPatientSummaryUseCase,
)
from fhir_gateway.domain.entities.condition import Condition
from fhir_gateway.domain.entities.encounter import Encounter
from fhir_gateway.domain.entities.observation import Observation, ObservationStatus
from fhir_gateway.domain.entities.patient import Patient
from fhir_gateway.domain.value_objects.code import Code
from fhir_gateway.domain.value_objects.human_name import HumanName
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.period import Period
from fhir_gateway.domain.value_objects.quantity import Quantity
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId


class InMemoryPatientReader:
    def __init__(self, patient: Patient | None) -> None:
        self.patient = patient
        self.received_patient_id: ResourceId | None = None

    def get_by_id(self, patient_id: ResourceId) -> Patient | None:
        self.received_patient_id = patient_id
        return self.patient


class InMemoryConditionReader:
    def __init__(self, conditions: tuple[Condition, ...]) -> None:
        self.conditions = conditions
        self.received_patient_id: ResourceId | None = None

    def list_by_patient(self, patient_id: ResourceId) -> tuple[Condition, ...]:
        self.received_patient_id = patient_id
        return self.conditions


class InMemoryEncounterReader:
    def __init__(self, encounters: tuple[Encounter, ...]) -> None:
        self.encounters = encounters
        self.received_patient_id: ResourceId | None = None

    def list_by_patient(self, patient_id: ResourceId) -> tuple[Encounter, ...]:
        self.received_patient_id = patient_id
        return self.encounters


class InMemoryObservationReader:
    def __init__(self, observations: tuple[Observation, ...]) -> None:
        self.observations = observations
        self.received_patient_id: ResourceId | None = None

    def list_by_patient(self, patient_id: ResourceId) -> tuple[Observation, ...]:
        self.received_patient_id = patient_id
        return self.observations


def _build_patient() -> Patient:
    return Patient(
        id=ResourceId("pat-001"),
        name=HumanName(given=("Ana",), family="García"),
    )


def _build_patient_reference() -> Reference:
    return Reference(resource_type="Patient", id=ResourceId("pat-001"))


def _build_instant(year: int, month: int, day: int) -> Instant:
    return Instant(
        value=datetime(year, month, day, 10, 0, 0, tzinfo=timezone.utc),
    )


def _build_condition() -> Condition:
    return Condition(
        id=ResourceId("con-001"),
        code=Code(
            system="http://snomed.info/sct",
            code="44054006",
            display="Diabetes mellitus type 2",
        ),
        subject=_build_patient_reference(),
        recorded_date=_build_instant(2026, 1, 15),
    )


def _build_encounter() -> Encounter:
    return Encounter(
        id=ResourceId("enc-001"),
        subject=_build_patient_reference(),
        period=Period(
            start=_build_instant(2026, 1, 10),
            end=_build_instant(2026, 1, 10),
        ),
    )


def _build_observation() -> Observation:
    return Observation(
        id=ResourceId("obs-001"),
        status=ObservationStatus.FINAL,
        code=Code(
            system="http://loinc.org",
            code="4548-4",
            display="Hemoglobin A1c/Hemoglobin.total in Blood",
        ),
        subject=_build_patient_reference(),
        effective=_build_instant(2026, 1, 12),
        value=Quantity(value=7.2, unit="%"),
    )


################################### VALID CASES:


def test_get_patient_summary_returns_structured_summary_with_resources():
    patient_id = ResourceId("pat-001")
    patient = _build_patient()
    condition = _build_condition()
    encounter = _build_encounter()
    observation = _build_observation()

    patient_reader = InMemoryPatientReader(patient=patient)
    condition_reader = InMemoryConditionReader(conditions=(condition,))
    encounter_reader = InMemoryEncounterReader(encounters=(encounter,))
    observation_reader = InMemoryObservationReader(observations=(observation,))

    use_case = GetPatientSummaryUseCase(
        patient_reader=patient_reader,
        condition_reader=condition_reader,
        encounter_reader=encounter_reader,
        observation_reader=observation_reader,
    )

    summary = use_case.execute(patient_id)

    assert summary.patient == patient
    assert summary.conditions == (condition,)
    assert summary.encounters == (encounter,)
    assert summary.observations == (observation,)


def test_get_patient_summary_accepts_empty_related_collections():
    patient_id = ResourceId("pat-001")
    patient = _build_patient()

    patient_reader = InMemoryPatientReader(patient=patient)
    condition_reader = InMemoryConditionReader(conditions=())
    encounter_reader = InMemoryEncounterReader(encounters=())
    observation_reader = InMemoryObservationReader(observations=())

    use_case = GetPatientSummaryUseCase(
        patient_reader=patient_reader,
        condition_reader=condition_reader,
        encounter_reader=encounter_reader,
        observation_reader=observation_reader,
    )

    summary = use_case.execute(patient_id)

    assert summary.patient == patient
    assert summary.conditions == ()
    assert summary.encounters == ()
    assert summary.observations == ()


def test_get_patient_summary_passes_patient_id_to_all_readers():
    patient_id = ResourceId("pat-001")
    patient = _build_patient()

    patient_reader = InMemoryPatientReader(patient=patient)
    condition_reader = InMemoryConditionReader(conditions=())
    encounter_reader = InMemoryEncounterReader(encounters=())
    observation_reader = InMemoryObservationReader(observations=())

    use_case = GetPatientSummaryUseCase(
        patient_reader=patient_reader,
        condition_reader=condition_reader,
        encounter_reader=encounter_reader,
        observation_reader=observation_reader,
    )

    use_case.execute(patient_id)

    assert patient_reader.received_patient_id == patient_id
    assert condition_reader.received_patient_id == patient_id
    assert encounter_reader.received_patient_id == patient_id
    assert observation_reader.received_patient_id == patient_id


################################### NOT VALID CASES:


def test_get_patient_summary_rejects_non_resource_id():
    use_case = GetPatientSummaryUseCase(
        patient_reader=InMemoryPatientReader(patient=None),
        condition_reader=InMemoryConditionReader(conditions=()),
        encounter_reader=InMemoryEncounterReader(encounters=()),
        observation_reader=InMemoryObservationReader(observations=()),
    )

    with pytest.raises(ApplicationValidationError) as exc:
        use_case.execute("pat-001")  # type: ignore[arg-type]

    assert exc.value.field == "GetPatientSummary.patient_id"
    assert exc.value.message == "must be a ResourceId"


def test_get_patient_summary_raises_not_found_when_patient_does_not_exist():
    patient_id = ResourceId("pat-999")

    use_case = GetPatientSummaryUseCase(
        patient_reader=InMemoryPatientReader(patient=None),
        condition_reader=InMemoryConditionReader(conditions=()),
        encounter_reader=InMemoryEncounterReader(encounters=()),
        observation_reader=InMemoryObservationReader(observations=()),
    )

    with pytest.raises(ApplicationNotFoundError) as exc:
        use_case.execute(patient_id)

    assert exc.value.resource == "Patient"
    assert exc.value.identifier == "pat-999"
    assert exc.value.message == "Patient not found: pat-999"
