from sqlalchemy import JSON, DateTime, UniqueConstraint

from fhir_gateway.infrastructure.persistence.sqlalchemy.base import Base
from fhir_gateway.infrastructure.persistence.sqlalchemy.mixins import TimestampMixin
from fhir_gateway.infrastructure.persistence.sqlalchemy.models.patient import (
    PatientIdentifierRecord,
    PatientRecord,
)


def test_patient_tables_are_registered_in_metadata():
    assert "patients" in Base.metadata.tables
    assert "patient_identifiers" in Base.metadata.tables


def test_patient_record_uses_timestamp_mixin():
    assert issubclass(PatientRecord, TimestampMixin)


def test_patients_table_has_expected_columns():
    table = PatientRecord.__table__

    assert set(table.columns.keys()) == {
        "id",
        "name_text",
        "name_family",
        "name_given",
        "created_at",
        "updated_at",
    }


def test_patients_table_has_expected_primary_key_and_nullable_columns():
    table = PatientRecord.__table__

    assert table.c.id.primary_key
    assert table.c.name_text.nullable
    assert table.c.name_family.nullable
    assert table.c.name_given.nullable
    assert not table.c.created_at.nullable
    assert not table.c.updated_at.nullable


def test_patients_table_uses_expected_column_types():
    table = PatientRecord.__table__

    assert isinstance(table.c.name_given.type, JSON)
    assert isinstance(table.c.created_at.type, DateTime)
    assert isinstance(table.c.updated_at.type, DateTime)
    assert table.c.created_at.type.timezone
    assert table.c.updated_at.type.timezone


def test_patients_timestamp_columns_keep_expected_defaults():
    table = PatientRecord.__table__

    assert table.c.created_at.server_default is not None
    assert table.c.updated_at.server_default is not None
    assert table.c.updated_at.onupdate is not None


def test_patient_identifiers_table_has_expected_columns():
    table = PatientIdentifierRecord.__table__

    assert set(table.columns.keys()) == {
        "id",
        "patient_id",
        "system",
        "value",
    }


def test_patient_identifiers_table_has_expected_primary_key_and_required_columns():
    table = PatientIdentifierRecord.__table__

    assert table.c.id.primary_key
    assert not table.c.patient_id.nullable
    assert not table.c.system.nullable
    assert not table.c.value.nullable


def test_patient_identifiers_table_references_patients_table():
    table = PatientIdentifierRecord.__table__

    foreign_keys = table.c.patient_id.foreign_keys

    assert len(foreign_keys) == 1

    foreign_key = next(iter(foreign_keys))

    assert str(foreign_key.column) == "patients.id"
    assert foreign_key.ondelete == "CASCADE"


def test_patient_identifiers_table_has_unique_patient_system_value_constraint():
    table = PatientIdentifierRecord.__table__

    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    unique_constraint_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in unique_constraints
    }

    assert ("patient_id", "system", "value") in unique_constraint_columns


def test_patient_identifiers_table_has_system_value_index():
    table = PatientIdentifierRecord.__table__

    indexes = {
        index.name: tuple(column.name for column in index.columns)
        for index in table.indexes
    }

    assert indexes["ix_patient_identifiers_system_value"] == ("system", "value")


def test_patient_record_has_identifiers_relationship():
    relationship_property = PatientRecord.identifiers.property

    assert relationship_property.mapper.class_ is PatientIdentifierRecord
    assert relationship_property.back_populates == "patient"
    assert "delete-orphan" in relationship_property.cascade


def test_patient_identifier_record_has_patient_relationship():
    relationship_property = PatientIdentifierRecord.patient.property

    assert relationship_property.mapper.class_ is PatientRecord
    assert relationship_property.back_populates == "identifiers"
