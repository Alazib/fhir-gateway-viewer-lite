from datetime import datetime, timezone

import pytest

from fhir_gateway.domain.entities.observation import Observation, ObservationStatus
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.value_objects.code import Code
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.quantity import Quantity
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId


################################### VALID CASES:


def test_accepts_valid_observation():
    observation = Observation(
        id=ResourceId("obs-001"),
        status=ObservationStatus.FINAL,
        code=Code(system="http://loinc.org", code="4548-4", display="HbA1c"),
        subject=Reference(resource_type="Patient", id=ResourceId("pat-001")),
        effective=Instant(value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)),
        value=Quantity(value=6.2, unit="%"),
    )

    assert observation.id.value == "obs-001"
    assert observation.status is ObservationStatus.FINAL
    assert observation.code.code == "4548-4"
    assert observation.subject.resource_type == "Patient"
    assert observation.subject.id.value == "pat-001"
    assert observation.effective.value == datetime(
        2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc
    )
    assert observation.value.value == 6.2
    assert observation.value.unit == "%"


def test_accepts_preliminary_observation():
    observation = Observation(
        id=ResourceId("obs-002"),
        status=ObservationStatus.PRELIMINARY,
        code=Code(system="http://loinc.org", code="2345-7", display="Glucose"),
        subject=Reference(resource_type="Patient", id=ResourceId("pat-001")),
        effective=Instant(value=datetime(2026, 2, 14, 11, 0, 0, tzinfo=timezone.utc)),
        value=Quantity(value=105, unit="mg/dL"),
    )

    assert observation.status is ObservationStatus.PRELIMINARY


################################### NOT VALID CASES:


def test_rejects_non_resource_id():
    with pytest.raises(DomainValidationError) as exc:
        Observation(
            id="obs-001",  # type: ignore[arg-type]
            status=ObservationStatus.FINAL,
            code=Code(system="http://loinc.org", code="4548-4", display="HbA1c"),
            subject=Reference(resource_type="Patient", id=ResourceId("pat-001")),
            effective=Instant(
                value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)
            ),
            value=Quantity(value=6.2, unit="%"),
        )

    assert exc.value.field == "Observation.id"
    assert exc.value.message == "must be a ResourceId"


def test_rejects_non_observation_status():
    with pytest.raises(DomainValidationError) as exc:
        Observation(
            id=ResourceId("obs-001"),
            status="final",  # type: ignore[arg-type]
            code=Code(system="http://loinc.org", code="4548-4", display="HbA1c"),
            subject=Reference(resource_type="Patient", id=ResourceId("pat-001")),
            effective=Instant(
                value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)
            ),
            value=Quantity(value=6.2, unit="%"),
        )

    assert exc.value.field == "Observation.status"
    assert exc.value.message == "must be an ObservationStatus"


def test_rejects_non_code():
    with pytest.raises(DomainValidationError) as exc:
        Observation(
            id=ResourceId("obs-001"),
            status=ObservationStatus.FINAL,
            code="4548-4",  # type: ignore[arg-type]
            subject=Reference(resource_type="Patient", id=ResourceId("pat-001")),
            effective=Instant(
                value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)
            ),
            value=Quantity(value=6.2, unit="%"),
        )

    assert exc.value.field == "Observation.code"
    assert exc.value.message == "must be a Code"


def test_rejects_non_reference():
    with pytest.raises(DomainValidationError) as exc:
        Observation(
            id=ResourceId("obs-001"),
            status=ObservationStatus.FINAL,
            code=Code(system="http://loinc.org", code="4548-4", display="HbA1c"),
            subject="Patient/pat-001",  # type: ignore[arg-type]
            effective=Instant(
                value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)
            ),
            value=Quantity(value=6.2, unit="%"),
        )

    assert exc.value.field == "Observation.subject"
    assert exc.value.message == "must be a Reference"


def test_rejects_subject_not_referencing_patient():
    with pytest.raises(DomainValidationError) as exc:
        Observation(
            id=ResourceId("obs-001"),
            status=ObservationStatus.FINAL,
            code=Code(system="http://loinc.org", code="4548-4", display="HbA1c"),
            subject=Reference(resource_type="Observation", id=ResourceId("obs-999")),
            effective=Instant(
                value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)
            ),
            value=Quantity(value=6.2, unit="%"),
        )

    assert exc.value.field == "Observation.subject"
    assert exc.value.message == "must reference Patient"


def test_rejects_non_instant():
    with pytest.raises(DomainValidationError) as exc:
        Observation(
            id=ResourceId("obs-001"),
            status=ObservationStatus.FINAL,
            code=Code(system="http://loinc.org", code="4548-4", display="HbA1c"),
            subject=Reference(resource_type="Patient", id=ResourceId("pat-001")),
            effective=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc),  # type: ignore[arg-type]
            value=Quantity(value=6.2, unit="%"),
        )

    assert exc.value.field == "Observation.effective"
    assert exc.value.message == "must be an Instant"


def test_rejects_non_quantity():
    with pytest.raises(DomainValidationError) as exc:
        Observation(
            id=ResourceId("obs-001"),
            status=ObservationStatus.FINAL,
            code=Code(system="http://loinc.org", code="4548-4", display="HbA1c"),
            subject=Reference(resource_type="Patient", id=ResourceId("pat-001")),
            effective=Instant(
                value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)
            ),
            value="6.2 %",  # type: ignore[arg-type]
        )

    assert exc.value.field == "Observation.value"
    assert exc.value.message == "must be a Quantity"
