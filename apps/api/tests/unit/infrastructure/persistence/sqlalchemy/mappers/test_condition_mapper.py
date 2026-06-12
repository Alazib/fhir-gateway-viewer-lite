from datetime import datetime, timezone

import pytest

from fhir_gateway.domain.entities.condition import Condition
from fhir_gateway.domain.value_objects.code import Code
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.mappers.condition import (
    condition_record_to_domain,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.condition import (
    ConditionCodeRecord,
    ConditionRecord,
)


def _condition_record(
    *,
    code_id: int = 1,
    recorded_at: datetime | None = datetime(
        2026,
        6,
        4,
        10,
        0,
        tzinfo=timezone.utc,
    ),
) -> ConditionRecord:
    return ConditionRecord(
        id="cond-001",
        patient_id="pat-001",
        code_id=code_id,
        recorded_at=recorded_at,
    )


def _condition_code_record(*, id: int = 1) -> ConditionCodeRecord:
    return ConditionCodeRecord(
        id=id,
        system="http://snomed.info/sct",
        code="44054006",
        display="Diabetes mellitus type 2",
    )


def test_condition_record_to_domain_returns_condition():
    record = _condition_record()
    code_record = _condition_code_record()

    condition = condition_record_to_domain(record, code_record)

    assert isinstance(condition, Condition)


def test_condition_record_to_domain_maps_id_to_resource_id():
    record = _condition_record()
    code_record = _condition_code_record()

    condition = condition_record_to_domain(record, code_record)

    assert condition.id == ResourceId("cond-001")


def test_condition_record_to_domain_maps_code_catalog_record_to_code():
    record = _condition_record()
    code_record = _condition_code_record()

    condition = condition_record_to_domain(record, code_record)

    assert condition.code == Code(
        system="http://snomed.info/sct",
        code="44054006",
        display="Diabetes mellitus type 2",
    )


def test_condition_record_to_domain_maps_patient_reference():
    record = _condition_record()
    code_record = _condition_code_record()

    condition = condition_record_to_domain(record, code_record)

    assert condition.subject == Reference(
        resource_type="Patient",
        id=ResourceId("pat-001"),
    )


def test_condition_record_to_domain_maps_recorded_at_to_recorded_date():
    recorded_at = datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc)

    record = _condition_record(recorded_at=recorded_at)
    code_record = _condition_code_record()

    condition = condition_record_to_domain(record, code_record)

    assert condition.recorded_date == Instant(recorded_at)


def test_condition_record_to_domain_maps_null_recorded_at_to_none():
    record = _condition_record(recorded_at=None)
    code_record = _condition_code_record()

    condition = condition_record_to_domain(record, code_record)

    assert condition.recorded_date is None


def test_condition_record_to_domain_rejects_mismatched_code_record():
    record = _condition_record(code_id=1)
    code_record = _condition_code_record(id=2)

    with pytest.raises(ValueError) as exc_info:
        condition_record_to_domain(record, code_record)

    assert (
        str(exc_info.value)
        == "ConditionRecord.code_id must match ConditionCodeRecord.id"
    )


def test_condition_record_to_domain_ignores_technical_metadata():
    timestamp = datetime(2026, 6, 4, 11, 0, tzinfo=timezone.utc)

    record = ConditionRecord(
        id="cond-001",
        patient_id="pat-001",
        code_id=1,
        recorded_at=datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc),
        created_at=timestamp,
        updated_at=timestamp,
        deleted_at=timestamp,
    )
    code_record = _condition_code_record()

    condition = condition_record_to_domain(record, code_record)

    assert not hasattr(condition, "created_at")
    assert not hasattr(condition, "updated_at")
    assert not hasattr(condition, "deleted_at")
