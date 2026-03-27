from datetime import datetime, timezone

import pytest

from fhir_gateway.domain.entities.condition import Condition
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.value_objects.code import Code
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId


################################### VALID CASES:


def test_accepts_valid_condition_without_recorded_date():
    condition = Condition(
        id=ResourceId("con-001"),
        code=Code(
            system="http://snomed.info/sct",
            code="44054006",
            display="Diabetes mellitus type 2",
        ),
        subject=Reference(resource_type="Patient", id=ResourceId("pat-001")),
        recorded_date=None,
    )

    assert condition.id.value == "con-001"
    assert condition.code.code == "44054006"
    assert condition.subject.resource_type == "Patient"
    assert condition.subject.id.value == "pat-001"
    assert condition.recorded_date is None


def test_accepts_valid_condition_with_recorded_date():
    recorded = Instant(value=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc))
    condition = Condition(
        id=ResourceId("con-002"),
        code=Code(
            system="http://snomed.info/sct",
            code="44054006",
            display="Diabetes mellitus type 2",
        ),
        subject=Reference(resource_type="Patient", id=ResourceId("pat-001")),
        recorded_date=recorded,
    )

    assert condition.recorded_date == recorded


################################### NOT VALID CASES:


def test_rejects_non_resource_id():
    with pytest.raises(DomainValidationError) as exc:
        Condition(
            id="con-001",  # type: ignore[arg-type]
            code=Code(
                system="http://snomed.info/sct",
                code="44054006",
                display="Diabetes mellitus type 2",
            ),
            subject=Reference(resource_type="Patient", id=ResourceId("pat-001")),
        )

    assert exc.value.field == "Condition.id"
    assert exc.value.message == "must be a ResourceId"


def test_rejects_non_code():
    with pytest.raises(DomainValidationError) as exc:
        Condition(
            id=ResourceId("con-001"),
            code="44054006",  # type: ignore[arg-type]
            subject=Reference(resource_type="Patient", id=ResourceId("pat-001")),
        )

    assert exc.value.field == "Condition.code"
    assert exc.value.message == "must be a Code"


def test_rejects_non_reference():
    with pytest.raises(DomainValidationError) as exc:
        Condition(
            id=ResourceId("con-001"),
            code=Code(
                system="http://snomed.info/sct",
                code="44054006",
                display="Diabetes mellitus type 2",
            ),
            subject="Patient/pat-001",  # type: ignore[arg-type]
        )

    assert exc.value.field == "Condition.subject"
    assert exc.value.message == "must be a Reference"


def test_rejects_subject_not_referencing_patient():
    with pytest.raises(DomainValidationError) as exc:
        Condition(
            id=ResourceId("con-001"),
            code=Code(
                system="http://snomed.info/sct",
                code="44054006",
                display="Diabetes mellitus type 2",
            ),
            subject=Reference(resource_type="Observation", id=ResourceId("obs-999")),
        )

    assert exc.value.field == "Condition.subject"
    assert exc.value.message == "must reference Patient"


def test_rejects_non_instant_recorded_date():
    with pytest.raises(DomainValidationError) as exc:
        Condition(
            id=ResourceId("con-001"),
            code=Code(
                system="http://snomed.info/sct",
                code="44054006",
                display="Diabetes mellitus type 2",
            ),
            subject=Reference(resource_type="Patient", id=ResourceId("pat-001")),
            recorded_date=datetime(2026, 2, 14, 10, 0, 0, tzinfo=timezone.utc),  # type: ignore[arg-type]
        )

    assert exc.value.field == "Condition.recorded_date"
    assert exc.value.message == "must be an Instant"
