from datetime import datetime, timezone

import pytest

from fhir_gateway.domain.entities.observation import (
    Observation,
    ObservationStatus,
)
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.value_objects.code import Code
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.quantity import Quantity
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.mappers.observation import (
    observation_record_to_domain,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.observation import (
    ObservationCodeRecord,
    ObservationRecord,
)


def _observation_record(
    *,
    code_id: int = 1,
    status: str = "final",
    value_quantity: float | None = 5.4,
    value_unit: str | None = "mg/dL",
) -> ObservationRecord:
    return ObservationRecord(
        id="obs-001",
        patient_id="pat-001",
        status=status,
        code_id=code_id,
        effective_at=datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc),
        value_quantity=value_quantity,
        value_unit=value_unit,
    )


def _observation_code_record(*, id: int = 1) -> ObservationCodeRecord:
    return ObservationCodeRecord(
        id=id,
        system="http://loinc.org",
        code="2339-0",
        display="Glucose",
    )


def test_observation_record_to_domain_returns_observation():
    record = _observation_record()
    code_record = _observation_code_record()

    observation = observation_record_to_domain(record, code_record)

    assert isinstance(observation, Observation)


def test_observation_record_to_domain_maps_id_to_resource_id():
    record = _observation_record()
    code_record = _observation_code_record()

    observation = observation_record_to_domain(record, code_record)

    assert observation.id == ResourceId("obs-001")


def test_observation_record_to_domain_maps_status_to_observation_status():
    record = _observation_record(status="final")
    code_record = _observation_code_record()

    observation = observation_record_to_domain(record, code_record)

    assert observation.status is ObservationStatus.FINAL


def test_observation_record_to_domain_maps_code_catalog_record_to_code():
    record = _observation_record()
    code_record = _observation_code_record()

    observation = observation_record_to_domain(record, code_record)

    assert observation.code == Code(
        system="http://loinc.org",
        code="2339-0",
        display="Glucose",
    )


def test_observation_record_to_domain_maps_patient_reference():
    record = _observation_record()
    code_record = _observation_code_record()

    observation = observation_record_to_domain(record, code_record)

    assert observation.subject == Reference(
        resource_type="Patient",
        id=ResourceId("pat-001"),
    )


def test_observation_record_to_domain_maps_effective_at_to_instant():
    effective_at = datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc)

    record = ObservationRecord(
        id="obs-001",
        patient_id="pat-001",
        status="final",
        code_id=1,
        effective_at=effective_at,
        value_quantity=5.4,
        value_unit="mg/dL",
    )
    code_record = _observation_code_record()

    observation = observation_record_to_domain(record, code_record)

    assert observation.effective == Instant(effective_at)


def test_observation_record_to_domain_maps_quantity_with_value_and_unit():
    record = _observation_record(
        value_quantity=5.4,
        value_unit="mg/dL",
    )
    code_record = _observation_code_record()

    observation = observation_record_to_domain(record, code_record)

    assert observation.value == Quantity(
        value=5.4,
        unit="mg/dL",
    )


def test_observation_record_to_domain_maps_missing_quantity_to_empty_quantity():
    record = _observation_record(
        value_quantity=None,
        value_unit=None,
    )
    code_record = _observation_code_record()

    observation = observation_record_to_domain(record, code_record)

    assert observation.value == Quantity()


def test_observation_record_to_domain_rejects_quantity_value_without_unit():
    record = _observation_record(
        value_quantity=5.4,
        value_unit=None,
    )
    code_record = _observation_code_record()

    with pytest.raises(DomainValidationError) as exc_info:
        observation_record_to_domain(record, code_record)

    assert exc_info.value.field == "Quantity.unit"


def test_observation_record_to_domain_rejects_invalid_status():
    record = _observation_record(status="invalid-status")
    code_record = _observation_code_record()

    with pytest.raises(ValueError):
        observation_record_to_domain(record, code_record)


def test_observation_record_to_domain_rejects_mismatched_code_record():
    record = _observation_record(code_id=1)
    code_record = _observation_code_record(id=2)

    with pytest.raises(ValueError) as exc_info:
        observation_record_to_domain(record, code_record)

    assert (
        str(exc_info.value)
        == "ObservationRecord.code_id must match ObservationCodeRecord.id"
    )


def test_observation_record_to_domain_ignores_technical_metadata():
    timestamp = datetime(2026, 6, 4, 11, 0, tzinfo=timezone.utc)

    record = ObservationRecord(
        id="obs-001",
        patient_id="pat-001",
        status="final",
        code_id=1,
        effective_at=datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc),
        value_quantity=5.4,
        value_unit="mg/dL",
        created_at=timestamp,
        updated_at=timestamp,
        deleted_at=timestamp,
    )
    code_record = _observation_code_record()

    observation = observation_record_to_domain(record, code_record)

    assert not hasattr(observation, "created_at")
    assert not hasattr(observation, "updated_at")
    assert not hasattr(observation, "deleted_at")
