from datetime import datetime, timezone

from fhir_gateway.domain.entities.encounter import Encounter
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.period import Period
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId
from fhir_gateway.infrastructure.persistence.sqlalchemy.mappers.encounter import (
    encounter_record_to_domain,
)
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.encounter import (
    EncounterRecord,
)


def test_encounter_record_to_domain_returns_encounter():
    record = EncounterRecord(
        id="enc-001",
        patient_id="pat-001",
        period_start_at=datetime(2026, 6, 4, 9, 0, tzinfo=timezone.utc),
        period_end_at=None,
    )

    encounter = encounter_record_to_domain(record)

    assert isinstance(encounter, Encounter)


def test_encounter_record_to_domain_maps_id_to_resource_id():
    record = EncounterRecord(
        id="enc-001",
        patient_id="pat-001",
        period_start_at=datetime(2026, 6, 4, 9, 0, tzinfo=timezone.utc),
        period_end_at=None,
    )

    encounter = encounter_record_to_domain(record)

    assert encounter.id == ResourceId("enc-001")


def test_encounter_record_to_domain_maps_patient_reference():
    record = EncounterRecord(
        id="enc-001",
        patient_id="pat-001",
        period_start_at=datetime(2026, 6, 4, 9, 0, tzinfo=timezone.utc),
        period_end_at=None,
    )

    encounter = encounter_record_to_domain(record)

    assert encounter.subject == Reference(
        resource_type="Patient",
        id=ResourceId("pat-001"),
    )


def test_encounter_record_to_domain_maps_period_without_end():
    start = datetime(2026, 6, 4, 9, 0, tzinfo=timezone.utc)

    record = EncounterRecord(
        id="enc-001",
        patient_id="pat-001",
        period_start_at=start,
        period_end_at=None,
    )

    encounter = encounter_record_to_domain(record)

    assert encounter.period == Period(
        start=Instant(start),
        end=None,
    )


def test_encounter_record_to_domain_maps_period_with_end():
    start = datetime(2026, 6, 4, 9, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 4, 9, 30, tzinfo=timezone.utc)

    record = EncounterRecord(
        id="enc-001",
        patient_id="pat-001",
        period_start_at=start,
        period_end_at=end,
    )

    encounter = encounter_record_to_domain(record)

    assert encounter.period == Period(
        start=Instant(start),
        end=Instant(end),
    )


def test_encounter_record_to_domain_ignores_technical_metadata():
    timestamp = datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc)

    record = EncounterRecord(
        id="enc-001",
        patient_id="pat-001",
        period_start_at=datetime(2026, 6, 4, 9, 0, tzinfo=timezone.utc),
        period_end_at=None,
        created_at=timestamp,
        updated_at=timestamp,
        deleted_at=timestamp,
    )

    encounter = encounter_record_to_domain(record)

    assert not hasattr(encounter, "created_at")
    assert not hasattr(encounter, "updated_at")
    assert not hasattr(encounter, "deleted_at")
