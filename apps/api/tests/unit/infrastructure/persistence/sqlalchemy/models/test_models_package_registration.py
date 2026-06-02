from fhir_gateway.infrastructure.persistence.sqlalchemy import models
from fhir_gateway.infrastructure.persistence.sqlalchemy.base import Base


EXPECTED_MODEL_TABLES = {
    "ConditionCodeRecord": "condition_codes",
    "ConditionRecord": "conditions",
    "EncounterRecord": "encounters",
    "ObservationCodeRecord": "observation_codes",
    "ObservationRecord": "observations",
    "PatientIdentifierRecord": "patient_identifiers",
    "PatientRecord": "patients",
}


def test_models_package_exports_all_expected_orm_records():
    assert set(models.__all__) == set(EXPECTED_MODEL_TABLES.keys())


def test_models_package_exposes_all_expected_orm_record_classes():
    for model_name in EXPECTED_MODEL_TABLES:
        assert hasattr(models, model_name)


def test_importing_models_package_registers_all_expected_tables_in_metadata():
    expected_table_names = set(EXPECTED_MODEL_TABLES.values())

    assert expected_table_names.issubset(set(Base.metadata.tables.keys()))


def test_exported_orm_records_point_to_expected_table_names():
    for model_name, expected_table_name in EXPECTED_MODEL_TABLES.items():
        model_class = getattr(models, model_name)

        assert model_class.__tablename__ == expected_table_name
        assert model_class.__table__ is Base.metadata.tables[expected_table_name]
