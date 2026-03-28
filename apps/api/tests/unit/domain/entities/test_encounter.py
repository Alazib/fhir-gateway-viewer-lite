from datetime import datetime, timezone

import pytest

from fhir_gateway.domain.entities.encounter import Encounter
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.period import Period
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId


################################### VALID CASES:


def test_accepts_valid_encounter_with_open_period():
    encounter = Encounter(
        id=ResourceId("enc-001"),
        subject=Reference(resource_type="Patient", id=ResourceId("pat-001")),
        period=Period(
            start=Instant(value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)),
            end=None,
        ),
    )

    assert encounter.id.value == "enc-001"
    assert encounter.subject.resource_type == "Patient"
    assert encounter.subject.id.value == "pat-001"
    assert encounter.period.start is not None
    assert encounter.period.end is None


def test_accepts_valid_encounter_with_closed_period():
    encounter = Encounter(
        id=ResourceId("enc-002"),
        subject=Reference(resource_type="Patient", id=ResourceId("pat-001")),
        period=Period(
            start=Instant(value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)),
            end=Instant(value=datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)),
        ),
    )

    assert encounter.period.start is not None
    assert encounter.period.end is not None


################################### NOT VALID CASES:


def test_rejects_non_resource_id():
    with pytest.raises(DomainValidationError) as exc:
        Encounter(
            id="enc-001",  # type: ignore[arg-type]
            subject=Reference(resource_type="Patient", id=ResourceId("pat-001")),
            period=Period(
                start=Instant(
                    value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)
                )
            ),
        )

    assert exc.value.field == "Encounter.id"
    assert exc.value.message == "must be a ResourceId"


def test_rejects_non_reference():
    with pytest.raises(DomainValidationError) as exc:
        Encounter(
            id=ResourceId("enc-001"),
            subject="Patient/pat-001",  # type: ignore[arg-type]
            period=Period(
                start=Instant(
                    value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)
                )
            ),
        )

    assert exc.value.field == "Encounter.subject"
    assert exc.value.message == "must be a Reference"


def test_rejects_subject_not_referencing_patient():
    with pytest.raises(DomainValidationError) as exc:
        Encounter(
            id=ResourceId("enc-001"),
            subject=Reference(resource_type="Observation", id=ResourceId("obs-999")),
            period=Period(
                start=Instant(
                    value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc)
                )
            ),
        )

    assert exc.value.field == "Encounter.subject"
    assert exc.value.message == "must reference Patient"


def test_rejects_non_period():
    with pytest.raises(DomainValidationError) as exc:
        Encounter(
            id=ResourceId("enc-001"),
            subject=Reference(resource_type="Patient", id=ResourceId("pat-001")),
            period="2026-02-14/2026-02-15",  # type: ignore[arg-type]
        )

    assert exc.value.field == "Encounter.period"
    assert exc.value.message == "must be a Period"


def test_rejects_period_without_start():
    with pytest.raises(DomainValidationError) as exc:
        Encounter(
            id=ResourceId("enc-001"),
            subject=Reference(resource_type="Patient", id=ResourceId("pat-001")),
            period=Period(
                start=None,
                end=Instant(value=datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)),
            ),
        )

    assert exc.value.field == "Encounter.period"
    assert exc.value.message == "start must be present"
