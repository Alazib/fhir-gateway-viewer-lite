from datetime import datetime, timezone

import pytest

from fhir_gateway.application.errors import (
    ApplicationNotFoundError,
    ApplicationValidationError,
)
from fhir_gateway.application.models.patient_bundle import PatientBundle
from fhir_gateway.application.use_cases.export_patient_bundle import (
    ExportPatientBundleUseCase,
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
        self.call_count = 0

    def list_by_patient(self, patient_id: ResourceId) -> tuple[Condition, ...]:
        self.call_count += 1
        self.received_patient_id = patient_id
        return self.conditions


class InMemoryEncounterReader:
    def __init__(self, encounters: tuple[Encounter, ...]) -> None:
        self.encounters = encounters
        self.received_patient_id: ResourceId | None = None
        self.call_count = 0

    def list_by_patient(self, patient_id: ResourceId) -> tuple[Encounter, ...]:
        self.call_count += 1
        self.received_patient_id = patient_id
        return self.encounters


class InMemoryObservationReader:
    def __init__(self, observations: tuple[Observation, ...]) -> None:
        self.observations = observations
        self.received_patient_id: ResourceId | None = None
        self.call_count = 0

    def list_by_patient(self, patient_id: ResourceId) -> tuple[Observation, ...]:
        self.call_count += 1
        self.received_patient_id = patient_id
        return self.observations


def _build_patient() -> Patient:
    return Patient(
        id=ResourceId("pat-001"),
        name=HumanName(given=("Ana",), family="García"),
    )


def _build_patient_reference() -> Reference:
    return Reference(
        resource_type="Patient",
        id=ResourceId("pat-001"),
    )


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


###################################
# PATIENT BUNDLE MODEL:


def test_patient_bundle_accepts_valid_resources():
    patient = _build_patient()
    condition = _build_condition()
    encounter = _build_encounter()
    observation = _build_observation()

    bundle = PatientBundle(
        patient=patient,
        conditions=(condition,),
        encounters=(encounter,),
        observations=(observation,),
    )

    assert bundle.patient == patient
    assert bundle.conditions == (condition,)
    assert bundle.encounters == (encounter,)
    assert bundle.observations == (observation,)


def test_patient_bundle_normalizes_lists_to_tuples():
    patient = _build_patient()
    condition = _build_condition()
    encounter = _build_encounter()
    observation = _build_observation()

    bundle = PatientBundle(
        patient=patient,
        conditions=[condition],  # type: ignore[arg-type]
        encounters=[encounter],  # type: ignore[arg-type]
        observations=[observation],  # type: ignore[arg-type]
    )

    assert bundle.conditions == (condition,)
    assert bundle.encounters == (encounter,)
    assert bundle.observations == (observation,)


def test_patient_bundle_rejects_invalid_patient():
    with pytest.raises(ApplicationValidationError) as exc:
        PatientBundle(
            patient="pat-001",  # type: ignore[arg-type]
            conditions=(),
            encounters=(),
            observations=(),
        )

    assert exc.value.field == "PatientBundle.patient"
    assert exc.value.message == "must be a Patient"


def test_patient_bundle_rejects_non_collection_conditions():
    patient = _build_patient()

    with pytest.raises(ApplicationValidationError) as exc:
        PatientBundle(
            patient=patient,
            conditions="not-a-collection",  # type: ignore[arg-type]
            encounters=(),
            observations=(),
        )

    assert exc.value.field == "PatientBundle.conditions"
    assert exc.value.message == "must be a list or a tuple of Condition"


def test_patient_bundle_rejects_invalid_condition_items():
    patient = _build_patient()

    with pytest.raises(ApplicationValidationError) as exc:
        PatientBundle(
            patient=patient,
            conditions=("not-a-condition",),  # type: ignore[arg-type]
            encounters=(),
            observations=(),
        )

    assert exc.value.field == "PatientBundle.conditions"
    assert exc.value.message == "must contain only Condition"


def test_patient_bundle_rejects_invalid_encounter_items():
    patient = _build_patient()

    with pytest.raises(ApplicationValidationError) as exc:
        PatientBundle(
            patient=patient,
            conditions=(),
            encounters=("not-an-encounter",),  # type: ignore[arg-type]
            observations=(),
        )

    assert exc.value.field == "PatientBundle.encounters"
    assert exc.value.message == "must contain only Encounter"


def test_patient_bundle_rejects_invalid_observation_items():
    patient = _build_patient()

    with pytest.raises(ApplicationValidationError) as exc:
        PatientBundle(
            patient=patient,
            conditions=(),
            encounters=(),
            observations=("not-an-observation",),  # type: ignore[arg-type]
        )

    assert exc.value.field == "PatientBundle.observations"
    assert exc.value.message == "must contain only Observation"


###################################
# USE CASE VALID CASES:


def test_export_patient_bundle_returns_structured_bundle_with_resources():
    patient_id = ResourceId("pat-001")

    patient = _build_patient()
    condition = _build_condition()
    encounter = _build_encounter()
    observation = _build_observation()

    patient_reader = InMemoryPatientReader(patient=patient)
    condition_reader = InMemoryConditionReader(conditions=(condition,))
    encounter_reader = InMemoryEncounterReader(encounters=(encounter,))
    observation_reader = InMemoryObservationReader(observations=(observation,))

    use_case = ExportPatientBundleUseCase(
        patient_reader=patient_reader,
        condition_reader=condition_reader,
        encounter_reader=encounter_reader,
        observation_reader=observation_reader,
    )

    bundle = use_case.execute(patient_id)

    assert bundle.patient == patient
    assert bundle.conditions == (condition,)
    assert bundle.encounters == (encounter,)
    assert bundle.observations == (observation,)


def test_export_patient_bundle_accepts_empty_related_collections():
    patient_id = ResourceId("pat-001")
    patient = _build_patient()

    patient_reader = InMemoryPatientReader(patient=patient)
    condition_reader = InMemoryConditionReader(conditions=())
    encounter_reader = InMemoryEncounterReader(encounters=())
    observation_reader = InMemoryObservationReader(observations=())

    use_case = ExportPatientBundleUseCase(
        patient_reader=patient_reader,
        condition_reader=condition_reader,
        encounter_reader=encounter_reader,
        observation_reader=observation_reader,
    )

    bundle = use_case.execute(patient_id)

    assert bundle.patient == patient
    assert bundle.conditions == ()
    assert bundle.encounters == ()
    assert bundle.observations == ()


def test_export_patient_bundle_passes_patient_id_to_all_readers():
    patient_id = ResourceId("pat-001")
    patient = _build_patient()

    patient_reader = InMemoryPatientReader(patient=patient)
    condition_reader = InMemoryConditionReader(conditions=())
    encounter_reader = InMemoryEncounterReader(encounters=())
    observation_reader = InMemoryObservationReader(observations=())

    use_case = ExportPatientBundleUseCase(
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


###################################
# USE CASE NOT VALID CASES:


def test_export_patient_bundle_rejects_non_resource_id():
    use_case = ExportPatientBundleUseCase(
        patient_reader=InMemoryPatientReader(patient=None),
        condition_reader=InMemoryConditionReader(conditions=()),
        encounter_reader=InMemoryEncounterReader(encounters=()),
        observation_reader=InMemoryObservationReader(observations=()),
    )

    with pytest.raises(ApplicationValidationError) as exc:
        use_case.execute("pat-001")  # type: ignore[arg-type]

    assert exc.value.field == "ExportPatientBundle.patient_id"
    assert exc.value.message == "must be a ResourceId"


def test_export_patient_bundle_raises_not_found_when_patient_does_not_exist():
    patient_id = ResourceId("pat-999")

    use_case = ExportPatientBundleUseCase(
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


def test_export_patient_bundle_does_not_call_related_readers_when_patient_does_not_exist():
    patient_id = ResourceId("pat-999")

    condition_reader = InMemoryConditionReader(conditions=())
    encounter_reader = InMemoryEncounterReader(encounters=())
    observation_reader = InMemoryObservationReader(observations=())

    use_case = ExportPatientBundleUseCase(
        patient_reader=InMemoryPatientReader(patient=None),
        condition_reader=condition_reader,
        encounter_reader=encounter_reader,
        observation_reader=observation_reader,
    )

    with pytest.raises(ApplicationNotFoundError):
        use_case.execute(patient_id)

    assert condition_reader.call_count == 0
    assert encounter_reader.call_count == 0
    assert observation_reader.call_count == 0
