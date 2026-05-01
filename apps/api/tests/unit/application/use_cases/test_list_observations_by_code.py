from datetime import datetime, timezone

import pytest

from fhir_gateway.application.errors import (
    ApplicationNotFoundError,
    ApplicationValidationError,
)
from fhir_gateway.application.use_cases.list_observations_by_code import (
    ListObservationsByCodeUseCase,
)
from fhir_gateway.domain.entities.observation import Observation, ObservationStatus
from fhir_gateway.domain.entities.patient import Patient
from fhir_gateway.domain.value_objects.code import Code
from fhir_gateway.domain.value_objects.human_name import HumanName
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.quantity import Quantity
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId


class InMemoryPatientReader:
    def __init__(self, patients: tuple[Patient, ...]) -> None:
        self.patients = patients
        self.received_patient_id: ResourceId | None = None

    def get_by_id(self, patient_id: ResourceId) -> Patient | None:
        self.received_patient_id = patient_id

        for patient in self.patients:
            if patient.id == patient_id:
                return patient

        return None


class InMemoryObservationByCodeReader:
    def __init__(self, observations: tuple[Observation, ...]) -> None:
        self.observations = observations
        self.received_patient_id: ResourceId | None = None
        self.received_code: Code | None = None
        self.call_count = 0

    def list_by_patient_and_code(
        self,
        patient_id: ResourceId,
        code: Code,
    ) -> tuple[Observation, ...]:
        self.call_count += 1
        self.received_patient_id = patient_id
        self.received_code = code

        return tuple(
            observation
            for observation in self.observations
            if observation.subject.id == patient_id
            and observation.code.system == code.system
            and observation.code.code == code.code
        )


def _build_patient(
    patient_id: str = "pat-001",
    given: str = "Ana",
    family: str = "García",
) -> Patient:
    return Patient(
        id=ResourceId(patient_id),
        name=HumanName(given=(given,), family=family),
    )


def _build_patient_reference(patient_id: str = "pat-001") -> Reference:
    return Reference(
        resource_type="Patient",
        id=ResourceId(patient_id),
    )


def _build_instant(year: int, month: int, day: int) -> Instant:
    return Instant(
        value=datetime(year, month, day, 10, 0, 0, tzinfo=timezone.utc),
    )


def _build_hba1c_code(
    display: str | None = "Hemoglobin A1c/Hemoglobin.total in Blood",
) -> Code:
    return Code(
        system="http://loinc.org",
        code="4548-4",
        display=display,
    )


def _build_ldl_code() -> Code:
    return Code(
        system="http://loinc.org",
        code="13457-7",
        display="LDL cholesterol",
    )


def _build_observation(
    observation_id: str,
    patient_id: str,
    code: Code,
    value: float,
    unit: str,
    year: int,
    month: int,
    day: int,
) -> Observation:
    return Observation(
        id=ResourceId(observation_id),
        status=ObservationStatus.FINAL,
        code=code,
        subject=_build_patient_reference(patient_id),
        effective=_build_instant(year, month, day),
        value=Quantity(value=value, unit=unit),
    )


###################################
# VALID CASES:


def test_list_observations_by_code_returns_matching_observations():
    patient_id = ResourceId("pat-001")
    hba1c_code = _build_hba1c_code()

    patient = _build_patient("pat-001")

    first_hba1c = _build_observation(
        observation_id="obs-001",
        patient_id="pat-001",
        code=hba1c_code,
        value=7.2,
        unit="%",
        year=2026,
        month=1,
        day=10,
    )
    second_hba1c = _build_observation(
        observation_id="obs-002",
        patient_id="pat-001",
        code=hba1c_code,
        value=6.8,
        unit="%",
        year=2026,
        month=3,
        day=10,
    )
    ldl_observation = _build_observation(
        observation_id="obs-003",
        patient_id="pat-001",
        code=_build_ldl_code(),
        value=130,
        unit="mg/dL",
        year=2026,
        month=2,
        day=5,
    )
    other_patient_hba1c = _build_observation(
        observation_id="obs-004",
        patient_id="pat-002",
        code=hba1c_code,
        value=8.1,
        unit="%",
        year=2026,
        month=1,
        day=20,
    )

    patient_reader = InMemoryPatientReader(patients=(patient,))
    observation_reader = InMemoryObservationByCodeReader(
        observations=(
            first_hba1c,
            second_hba1c,
            ldl_observation,
            other_patient_hba1c,
        ),
    )

    use_case = ListObservationsByCodeUseCase(
        patient_reader=patient_reader,
        observation_by_code_reader=observation_reader,
    )

    result = use_case.execute(patient_id, hba1c_code)

    assert result == (first_hba1c, second_hba1c)


def test_list_observations_by_code_returns_empty_tuple_when_patient_exists_but_no_observations_match():
    patient_id = ResourceId("pat-001")
    hba1c_code = _build_hba1c_code()

    patient = _build_patient("pat-001")

    ldl_observation = _build_observation(
        observation_id="obs-001",
        patient_id="pat-001",
        code=_build_ldl_code(),
        value=130,
        unit="mg/dL",
        year=2026,
        month=2,
        day=5,
    )

    patient_reader = InMemoryPatientReader(patients=(patient,))
    observation_reader = InMemoryObservationByCodeReader(
        observations=(ldl_observation,),
    )

    use_case = ListObservationsByCodeUseCase(
        patient_reader=patient_reader,
        observation_by_code_reader=observation_reader,
    )

    result = use_case.execute(patient_id, hba1c_code)

    assert result == ()


def test_list_observations_by_code_matches_by_system_and_code_not_display():
    patient_id = ResourceId("pat-001")

    stored_hba1c_code = _build_hba1c_code(
        display="Hemoglobin A1c/Hemoglobin.total in Blood",
    )
    query_hba1c_code = _build_hba1c_code(display=None)

    patient = _build_patient("pat-001")

    observation = _build_observation(
        observation_id="obs-001",
        patient_id="pat-001",
        code=stored_hba1c_code,
        value=7.2,
        unit="%",
        year=2026,
        month=1,
        day=10,
    )

    patient_reader = InMemoryPatientReader(patients=(patient,))
    observation_reader = InMemoryObservationByCodeReader(
        observations=(observation,),
    )

    use_case = ListObservationsByCodeUseCase(
        patient_reader=patient_reader,
        observation_by_code_reader=observation_reader,
    )

    result = use_case.execute(patient_id, query_hba1c_code)

    assert result == (observation,)


def test_list_observations_by_code_passes_patient_id_and_code_to_reader():
    patient_id = ResourceId("pat-001")
    hba1c_code = _build_hba1c_code()
    patient = _build_patient("pat-001")

    patient_reader = InMemoryPatientReader(patients=(patient,))
    observation_reader = InMemoryObservationByCodeReader(observations=())

    use_case = ListObservationsByCodeUseCase(
        patient_reader=patient_reader,
        observation_by_code_reader=observation_reader,
    )

    use_case.execute(patient_id, hba1c_code)

    assert patient_reader.received_patient_id == patient_id
    assert observation_reader.received_patient_id == patient_id
    assert observation_reader.received_code == hba1c_code


###################################
# NOT VALID CASES:


def test_list_observations_by_code_rejects_non_resource_id():
    hba1c_code = _build_hba1c_code()

    use_case = ListObservationsByCodeUseCase(
        patient_reader=InMemoryPatientReader(patients=()),
        observation_by_code_reader=InMemoryObservationByCodeReader(observations=()),
    )

    with pytest.raises(ApplicationValidationError) as exc:
        use_case.execute("pat-001", hba1c_code)  # type: ignore[arg-type]

    assert exc.value.field == "ListObservationsByCode.patient_id"
    assert exc.value.message == "must be a ResourceId"


def test_list_observations_by_code_rejects_non_code():
    patient_id = ResourceId("pat-001")

    use_case = ListObservationsByCodeUseCase(
        patient_reader=InMemoryPatientReader(patients=()),
        observation_by_code_reader=InMemoryObservationByCodeReader(observations=()),
    )

    with pytest.raises(ApplicationValidationError) as exc:
        use_case.execute(patient_id, "4548-4")  # type: ignore[arg-type]

    assert exc.value.field == "ListObservationsByCode.code"
    assert exc.value.message == "must be a Code"


def test_list_observations_by_code_raises_not_found_when_patient_does_not_exist():
    patient_id = ResourceId("pat-999")
    hba1c_code = _build_hba1c_code()

    observation_reader = InMemoryObservationByCodeReader(observations=())

    use_case = ListObservationsByCodeUseCase(
        patient_reader=InMemoryPatientReader(patients=()),
        observation_by_code_reader=observation_reader,
    )

    with pytest.raises(ApplicationNotFoundError) as exc:
        use_case.execute(patient_id, hba1c_code)

    assert exc.value.resource == "Patient"
    assert exc.value.identifier == "pat-999"
    assert exc.value.message == "Patient not found: pat-999"


def test_list_observations_by_code_does_not_call_observation_reader_when_patient_does_not_exist():
    patient_id = ResourceId("pat-999")
    hba1c_code = _build_hba1c_code()

    observation_reader = InMemoryObservationByCodeReader(observations=())

    use_case = ListObservationsByCodeUseCase(
        patient_reader=InMemoryPatientReader(patients=()),
        observation_by_code_reader=observation_reader,
    )

    with pytest.raises(ApplicationNotFoundError):
        use_case.execute(patient_id, hba1c_code)

    assert observation_reader.call_count == 0
