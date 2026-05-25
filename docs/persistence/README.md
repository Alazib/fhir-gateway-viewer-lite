# FHIR Mini-Gateway Persistence Documentation

## Status

Current persistence status: **Phase 3 / Backend foundation**

The backend currently includes:

- SQLAlchemy ORM
- Alembic
- Psycopg 3
- centralized `database_url` setting
- SQLAlchemy declarative `Base`
- database engine/session factory helpers
- Alembic configuration
- initial Patient ORM schema
- initial manual Patient migration
- architecture boundary tests preventing SQLAlchemy imports in domain/application

Current clinical persistence schemas:

| Resource | Status |
|---|---|
| Patient | Implemented |
| Patient identifiers | Implemented |
| Observation | Pending |
| Condition | Pending |
| Encounter | Pending |
| AuditEvent | Pending |

No SQLAlchemy adapter has been implemented yet.

No ORM/domain mapper has been implemented yet.

No HTTP endpoint is currently backed by database persistence.

---

## Purpose

This document describes the persistence layer of the `FHIR Gateway Viewer Lite` backend.

It covers:

- persistence architecture
- SQLAlchemy structure
- Alembic migrations
- current ORM models
- current database schema
- persistence design principles
- current limitations
- future persistence work

API behavior and HTTP endpoint documentation live in:

    docs/api/README.md

---

## Architectural boundaries

Persistence belongs to the infrastructure layer.

The domain layer must not import:

- SQLAlchemy
- Alembic
- Psycopg
- ORM models
- database sessions
- database engine helpers

The application layer must not import:

- SQLAlchemy
- Alembic
- Psycopg
- ORM models
- database sessions
- database engine helpers

The intended dependency direction is:

    domain
        ↑
    application
        ↑
    infrastructure

Infrastructure may depend on domain and application.

Domain and application must not depend on infrastructure.

---

## Persistence structure

Current structure:

    apps/api/src/fhir_gateway/infrastructure/persistence/
    ├── __init__.py
    └── sqlalchemy/
        ├── __init__.py
        ├── base.py
        ├── database.py
        └── models/
            ├── __init__.py
            └── patient.py

Responsibilities:

- `base.py`: defines the SQLAlchemy declarative `Base`.
- `database.py`: provides helpers to create SQLAlchemy engines and session factories.
- `models/`: contains SQLAlchemy ORM models.
- `models/patient.py`: defines the initial Patient persistence records.

---

## Runtime database configuration

The database URL is defined in:

    apps/api/src/fhir_gateway/infrastructure/config/settings.py

Current setting:

| Setting | Environment variable | Default |
|---|---|---|
| `database_url` | `FHIR_GATEWAY_DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/fhir_gateway` |

Example PowerShell override:

    $env:FHIR_GATEWAY_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/fhir_gateway"

The default value is for local development only.

Production database credentials must be provided through environment variables or a future secrets management strategy.

---

## SQLAlchemy base

The SQLAlchemy declarative base is defined in:

    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/base.py

It exposes:

    Base.metadata

`Base.metadata` is the central SQLAlchemy registry of known tables.

Current clinical ORM tables registered in metadata:

    patients
    patient_identifiers

Alembic uses this metadata to understand the target schema.

---

## Database engine and session factory

Database helpers are defined in:

    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/database.py

Current helpers:

    create_database_engine(database_url)
    create_session_factory(engine)

Intended future flow:

    Settings.database_url
        -> create_database_engine(...)
        -> create_session_factory(...)
        -> SQLAlchemy infrastructure adapters

The API does not yet open database sessions for HTTP requests.

No request-scoped database session dependency exists yet.

That will be introduced later when persistence-backed use-cases are wired through HTTP.

---

## Current ORM models

Current ORM model module:

    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/models/patient.py

Defined ORM records:

    PatientRecord
    PatientIdentifierRecord

These records are persistence models.

They are not domain entities.

The domain entity remains:

    fhir_gateway.domain.entities.patient.Patient

The domain value objects remain:

    ResourceId
    Identifier
    HumanName

---

## Current Patient persistence schema

The first clinical persistence schema has been introduced for Patient.

Current database tables represented by SQLAlchemy metadata:

    patients
    patient_identifiers

---

## Table: `patients`

The `patients` table stores the persistence representation of the domain `Patient` root resource.

Current columns:

| Column | Type | Nullable | Purpose |
|---|---:|---:|---|
| `id` | string | no | Stores `ResourceId.value`; primary key |
| `name_text` | string | yes | Stores `HumanName.text` |
| `name_family` | string | yes | Stores `HumanName.family` |
| `name_given` | JSON | yes | Stores ordered `HumanName.given` values |
| `created_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `updated_at` | timezone-aware datetime | no | Technical persistence timestamp |

The timestamp columns are persistence metadata.

They are not part of the domain `Patient` entity at this stage.

---

## Table: `patient_identifiers`

The `patient_identifiers` table stores the persistence representation of `Patient.identifiers`.

Current columns:

| Column | Type | Nullable | Purpose |
|---|---:|---:|---|
| `id` | integer | no | Technical primary key |
| `patient_id` | string | no | Foreign key to `patients.id` |
| `system` | string | no | Identifier system |
| `value` | string | no | Identifier value |

Current constraints and indexes:

| Name | Type | Purpose |
|---|---|---|
| `uq_patient_identifiers_patient_system_value` | unique constraint | Prevents duplicate `(patient_id, system, value)` identifiers |
| `ix_patient_identifiers_system_value` | index | Supports future lookup by identifier system and value |

Foreign key:

    patient_identifiers.patient_id -> patients.id

Delete behavior:

    ON DELETE CASCADE

This means patient identifiers are dependent persistence records of a patient.

---

## Patient ORM relationship

Current relationship:

    PatientRecord 1 -> N PatientIdentifierRecord

`PatientRecord` owns a collection of identifier records.

The ORM relationship uses cascade/delete-orphan behavior so identifiers are treated as dependent records of the patient persistence record.

Conceptually:

    PatientRecord
        └── identifiers: list[PatientIdentifierRecord]

This relationship is persistence-level structure.

It is not the same thing as the domain entity itself.

A future mapper will translate:

    PatientRecord -> Patient

and, if needed:

    Patient -> PatientRecord

---

## Patient persistence design decisions

The current Patient persistence schema follows these rules:

1. `PatientRecord` is not the domain `Patient`.
2. `PatientIdentifierRecord` is not the domain `Identifier`.
3. `patients.id` stores `ResourceId.value`.
4. `patient_identifiers` stores repeated patient identifiers in a separate relational table.
5. `name_given` is stored as JSON to preserve ordered given names without introducing a premature `patient_given_names` table.
6. `created_at` and `updated_at` are technical persistence metadata.
7. Patient ORM records must be mapped to domain entities by infrastructure mappers in a later sub-issue.
8. Application use-cases must not return ORM records.
9. SQLAlchemy must remain isolated to infrastructure.

---

## Alembic migrations

Alembic has been initialized under:

    apps/api/alembic/

Current Alembic files:

    apps/api/
    ├── alembic.ini
    └── alembic/
        ├── env.py
        ├── script.py.mako
        └── versions/

Alembic is configured to use:

- `Settings.database_url`
- `Base.metadata`

The `alembic.ini` file prepends `src` to the Python path so Alembic can import the `fhir_gateway` package.

Alembic imports the SQLAlchemy models package so ORM models are registered in `Base.metadata`.

---

## Current migration status

A first manual migration exists under:

    apps/api/alembic/versions/

It creates:

    patients
    patient_identifiers

It also creates:

    uq_patient_identifiers_patient_system_value
    ix_patient_identifiers_system_value

The first Patient migration was created manually to make the schema explicit and reviewable.

Alembic autogeneration is intentionally deferred until the project has:

- a local PostgreSQL workflow
- multiple ORM models
- a clearer migration review routine

---

## Safe Alembic inspection commands

Show migration history:

    pipenv run alembic history --verbose

Render SQL without applying migrations:

    pipenv run alembic upgrade head --sql

The `--sql` command prints the SQL that Alembic would execute without applying it to the database.

Do not run database migrations yet unless a local PostgreSQL database has been created and configured.

Do not run this yet unless PostgreSQL is available and configured:

    pipenv run alembic upgrade head

---

## Manual migration note

The initial Patient migration was created manually.

This means the migration file intentionally repeats the schema already represented in the ORM models.

The two artifacts have different responsibilities:

- ORM models represent the current desired persistence shape.
- Alembic migrations represent historical steps to move the database from one schema version to another.

Manual migrations are useful for understanding the first schema, but they introduce the risk of divergence between ORM models and migration scripts.

For this reason, model tests and migration review are required.

Future work should introduce Alembic autogeneration plus manual review once the PostgreSQL workflow is ready.

---

## Timestamp strategy note

`created_at` and `updated_at` currently exist on the `patients` table as technical persistence metadata.

A database-wide timestamp and audit metadata strategy is intentionally deferred and tracked as:

    BACKLOG / HARDEN / P3 / Define database-wide timestamp and audit column strategy

This must be revisited after Patient plus one or two additional ORM models have been introduced, and before timestamp conventions are copied broadly across additional tables or SQLAlchemy adapters are consolidated.

This future work should likely produce an ADR covering:

- whether all persistence tables should include `created_at`
- whether all persistence tables should include `updated_at`
- whether timestamps should be timezone-aware
- whether timestamps should be generated by Python, SQLAlchemy, or the database
- whether server-side defaults or triggers should be used
- how generic row timestamps relate to the domain `AuditEvent`
- whether timestamp metadata should ever be exposed through HTTP APIs

Audit events are not the same thing as row timestamps.

Generic `created_at` and `updated_at` columns must not replace a real audit trail.

---

## Persistence tests

Run all persistence tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy

Run Patient ORM model tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models/test_patient_orm_models.py

Run architecture boundary tests:

    pipenv run pytest tests/unit/architecture

Run full test suite:

    pipenv run pytest

---

## Architecture boundary tests

The project includes an architecture boundary test that prevents SQLAlchemy imports in:

    domain/
    application/

Purpose:

- keep domain framework-agnostic
- keep application independent from persistence details
- ensure SQLAlchemy remains an infrastructure-only dependency

This protects the architectural decision documented in ADR 0012.

---

## Current limitations

The persistence layer does not yet include:

- Observation ORM model
- Condition ORM model
- Encounter ORM model
- AuditEvent ORM model
- ORM/domain mappers
- SQLAlchemy adapters for application ports
- request-scoped SQLAlchemy session management
- persistence-backed HTTP use-case wiring
- local PostgreSQL workflow
- Alembic autogeneration workflow
- migration integration tests
- seed data
- timestamp/audit metadata ADR

These capabilities are intentionally deferred.

---

## Planned persistence work

Likely next Phase 3 persistence sub-issues:

1. Add Observation, Condition, and Encounter ORM models and migration.
2. Add AuditEvent ORM model and migration.
3. Revisit database-wide timestamp and audit column strategy.
4. Add ORM/domain mappers.
5. Add SQLAlchemy adapters for application ports.
6. Wire selected persistence-backed use-cases through HTTP/dependencies.
7. Add local PostgreSQL workflow.
8. Add Alembic autogeneration workflow.
9. Add integration testing strategy for migrations and adapters.

---

## Persistence design principles

As persistence evolves:

1. Keep ORM models separate from domain entities.
2. Keep SQLAlchemy imports inside infrastructure.
3. Map ORM records to domain entities in infrastructure adapters or mappers.
4. Keep application ports expressed in domain/application types.
5. Use Alembic for schema changes.
6. Do not create tables manually outside migrations once migrations are active.
7. Do not expose ORM records directly from application use-cases.
8. Keep technical persistence metadata separate from domain meaning.
9. Revisit timestamp and audit metadata strategy before copying timestamp patterns broadly.
10. Do not allow persistence schemas to silently drive domain design.
11. Do not introduce broad generic repositories until repeated adapter duplication justifies it.

---

## Related ADRs

Current related ADRs:

- ADR 0012: SQLAlchemy persistence foundation and mapping boundaries
- ADR 0013: Centralized runtime configuration

Future expected ADR:

    Database-wide timestamp and audit metadata strategy

This ADR should be created before timestamp and audit conventions are repeated broadly across the persistence layer.
