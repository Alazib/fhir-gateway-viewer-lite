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
- constrained domain `Reference.resource_type`
- ADR 0014 database timestamp and audit metadata strategy

Current clinical persistence schemas:

| Resource / table group | Status |
|---|---|
| Patient | Implemented |
| Patient identifiers | Implemented |
| Observation codes | Planned in Sub-issue E |
| Condition codes | Planned in Sub-issue E |
| Observation | Planned in Sub-issue E |
| Condition | Planned in Sub-issue E |
| Encounter | Planned in Sub-issue E |
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
- planned clinical persistence schemas
- timestamp strategy
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

Planned structure after Sub-issue E:

    apps/api/src/fhir_gateway/infrastructure/persistence/
    ├── __init__.py
    └── sqlalchemy/
        ├── __init__.py
        ├── base.py
        ├── database.py
        ├── mixins.py
        └── models/
            ├── __init__.py
            ├── condition.py
            ├── encounter.py
            ├── observation.py
            └── patient.py

Responsibilities:

- `base.py`: defines the SQLAlchemy declarative `Base`.
- `database.py`: provides helpers to create SQLAlchemy engines and session factories.
- `mixins.py`: will contain reusable SQLAlchemy persistence mixins such as `TimestampMixin`.
- `models/`: contains SQLAlchemy ORM models.
- `models/patient.py`: defines the initial Patient persistence records.
- `models/observation.py`: will define Observation code catalog and Observation records.
- `models/condition.py`: will define Condition code catalog and Condition records.
- `models/encounter.py`: will define Encounter records.

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

Planned additional ORM tables after Sub-issue E:

    observation_codes
    condition_codes
    observations
    conditions
    encounters

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

## Timestamp strategy

Timestamp behavior is defined by:

    ADR 0014: Database timestamp and audit metadata strategy

Selected convention:

- `created_at` and `updated_at` are technical persistence metadata.
- They are not clinical dates.
- They are not audit events.
- Top-level ORM-managed tables should include `created_at` and `updated_at`.
- Dependent component tables do not receive timestamps by default.
- Domain entities do not receive `created_at` or `updated_at` by default.
- HTTP APIs do not expose technical timestamps by default.
- Phase 3 uses database server defaults plus SQLAlchemy `onupdate`.
- Database triggers are deferred to future hardening.
- A reusable SQLAlchemy `TimestampMixin` should be introduced.

Planned mixin:

    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/mixins.py

Planned class:

    TimestampMixin

Expected behavior:

    created_at:
        DateTime(timezone=True)
        server_default=func.now()
        nullable=False

    updated_at:
        DateTime(timezone=True)
        server_default=func.now()
        onupdate=func.now()
        nullable=False

Known limitation:

    Direct SQL updates outside SQLAlchemy may not update updated_at.

Trigger-based hardening is tracked separately:

    BACKLOG / HARDEN / P3+ / Add database triggers for updated_at consistency

---

## Technical timestamps vs clinical dates

Technical timestamps describe persistence operations in this application's database.

Examples:

    created_at
    updated_at

Clinical dates describe the domain meaning of a clinical resource.

Examples:

    Observation.effective
    Condition.recorded_date
    Encounter.period
    AuditEvent.recorded

Example distinction:

    observations.effective_at = 2026-05-20 08:30
    observations.created_at = 2026-05-26 12:00

Meaning:

    The observation was clinically effective on May 20.
    The observation row was inserted into this database on May 26.

Those are different facts.

Technical timestamps must not be confused with clinical dates.

---

## Technical timestamps vs audit events

Audit events describe actions performed in the system.

Examples:

    read
    search
    export

A future audit event may record:

    who performed the action
    what action was performed
    which entity was affected
    when the action happened

That is different from:

    created_at
    updated_at

Example:

    A user reads Patient pat-001 at 2026-05-26 18:42.

That should create or correspond to an audit event.

It should not necessarily update:

    patients.updated_at

Generic row timestamps are not a substitute for audit trail.

Audit events are not a substitute for generic row timestamps.

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

Planned ORM model modules for Sub-issue E:

    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/models/observation.py
    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/models/condition.py
    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/models/encounter.py

Planned ORM records for Sub-issue E:

    ObservationCodeRecord
    ConditionCodeRecord
    ObservationRecord
    ConditionRecord
    EncounterRecord

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

Sub-issue E must refactor `PatientRecord` to use `TimestampMixin` while preserving this effective schema.

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

According to ADR 0014, this dependent component table does not receive `created_at` and `updated_at` by default.

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
7. `patient_identifiers` does not receive timestamps by default because it is a dependent component table.
8. Patient ORM records must be mapped to domain entities by infrastructure mappers in a later sub-issue.
9. Application use-cases must not return ORM records.
10. SQLAlchemy must remain isolated to infrastructure.
11. Sub-issue E must refactor `PatientRecord` to use `TimestampMixin` without changing the effective schema.

---

## Planned Sub-issue E persistence schemas

Sub-issue E will introduce persistence schemas for:

    observation_codes
    condition_codes
    observations
    conditions
    encounters

These schemas are planned and not implemented yet.

Detailed implementation will happen in:

    PHASE 3 / SUB-ISSUE E / Add Observation, Condition, and Encounter ORM models and migration

---

## Planned table: `observation_codes`

The `observation_codes` table will store the catalog of supported/selectable Observation codes.

Current purpose:

    Future UI dropdowns.
    Consistent Observation code selection.
    Avoid repeated code data inside every observation row.

Planned columns:

| Column | Type | Nullable | Purpose |
|---|---:|---:|---|
| `id` | integer | no | Technical primary key |
| `system` | string | no | Code system |
| `code` | string | no | Code value |
| `display` | string | yes | Human-readable display |
| `created_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `updated_at` | timezone-aware datetime | no | Technical persistence timestamp |

Planned constraints:

| Name | Type | Columns |
|---|---|---|
| `uq_observation_codes_system_code` | unique constraint | `system`, `code` |

Notes:

- This table is a top-level ORM-managed catalog table.
- It should use `TimestampMixin`.
- It should not contain seed data in Sub-issue E.

---

## Planned table: `condition_codes`

The `condition_codes` table will store the catalog of supported/selectable Condition codes.

Current purpose:

    Future UI dropdowns.
    Consistent Condition code selection.
    Avoid repeated code data inside every condition row.

Planned columns:

| Column | Type | Nullable | Purpose |
|---|---:|---:|---|
| `id` | integer | no | Technical primary key |
| `system` | string | no | Code system |
| `code` | string | no | Code value |
| `display` | string | yes | Human-readable display |
| `created_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `updated_at` | timezone-aware datetime | no | Technical persistence timestamp |

Planned constraints:

| Name | Type | Columns |
|---|---|---|
| `uq_condition_codes_system_code` | unique constraint | `system`, `code` |

Notes:

- This table is a top-level ORM-managed catalog table.
- It should use `TimestampMixin`.
- It should not contain seed data in Sub-issue E.

---

## Planned table: `observations`

The `observations` table will store the persistence representation of the domain `Observation` resource.

Planned columns:

| Column | Type | Nullable | Purpose |
|---|---:|---:|---|
| `id` | string | no | Stores `ResourceId.value`; primary key |
| `patient_id` | string | no | Foreign key to `patients.id` |
| `status` | string | no | Observation status |
| `code_id` | integer | no | Foreign key to `observation_codes.id` |
| `effective_at` | timezone-aware datetime | no | Clinical effective datetime |
| `value_quantity` | float | yes | Quantity numeric value |
| `value_unit` | string | yes | Quantity unit |
| `created_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `updated_at` | timezone-aware datetime | no | Technical persistence timestamp |

Planned foreign keys:

| Column | References | Delete behavior |
|---|---|---|
| `patient_id` | `patients.id` | `ON DELETE CASCADE` |
| `code_id` | `observation_codes.id` | restrict/no cascade |

Planned constraints:

| Name | Type | Purpose |
|---|---|---|
| `ck_observations_status_allowed` | check constraint | Ensures status is one of the allowed `ObservationStatus` values |
| `ck_observations_value_quantity_requires_unit` | check constraint | Ensures `value_unit` is present when `value_quantity` is present |

Planned indexes:

| Name | Columns | Purpose |
|---|---|---|
| `ix_observations_patient_id` | `patient_id` | List observations for a patient |
| `ix_observations_patient_code` | `patient_id`, `code_id` | List observations for a patient by code |
| `ix_observations_patient_effective_at` | `patient_id`, `effective_at` | List/order observations for a patient by clinical date |

Allowed status values:

    registered
    preliminary
    final
    amended
    corrected
    cancelled
    entered-in-error
    unknown

Notes:

- `effective_at` is a clinical date, not a technical timestamp.
- `created_at` and `updated_at` are technical persistence metadata.
- `code_id` should not cascade-delete observations when a catalog row is deleted.
- This table should use `TimestampMixin`.

---

## Planned table: `conditions`

The `conditions` table will store the persistence representation of the domain `Condition` resource.

Planned columns:

| Column | Type | Nullable | Purpose |
|---|---:|---:|---|
| `id` | string | no | Stores `ResourceId.value`; primary key |
| `patient_id` | string | no | Foreign key to `patients.id` |
| `code_id` | integer | no | Foreign key to `condition_codes.id` |
| `recorded_at` | timezone-aware datetime | yes | Clinical recorded datetime |
| `created_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `updated_at` | timezone-aware datetime | no | Technical persistence timestamp |

Planned foreign keys:

| Column | References | Delete behavior |
|---|---|---|
| `patient_id` | `patients.id` | `ON DELETE CASCADE` |
| `code_id` | `condition_codes.id` | restrict/no cascade |

Planned indexes:

| Name | Columns | Purpose |
|---|---|---|
| `ix_conditions_patient_id` | `patient_id` | List conditions for a patient |
| `ix_conditions_patient_code` | `patient_id`, `code_id` | List/filter conditions for a patient by code |

Notes:

- `recorded_at` is nullable because `Condition.recorded_date` is optional in the domain.
- `created_at` and `updated_at` are technical persistence metadata.
- `code_id` should not cascade-delete conditions when a catalog row is deleted.
- This table should use `TimestampMixin`.

---

## Planned table: `encounters`

The `encounters` table will store the persistence representation of the domain `Encounter` resource.

Planned columns:

| Column | Type | Nullable | Purpose |
|---|---:|---:|---|
| `id` | string | no | Stores `ResourceId.value`; primary key |
| `patient_id` | string | no | Foreign key to `patients.id` |
| `period_start_at` | timezone-aware datetime | no | Clinical encounter period start |
| `period_end_at` | timezone-aware datetime | yes | Clinical encounter period end |
| `created_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `updated_at` | timezone-aware datetime | no | Technical persistence timestamp |

Planned foreign keys:

| Column | References | Delete behavior |
|---|---|---|
| `patient_id` | `patients.id` | `ON DELETE CASCADE` |

Planned constraints:

| Name | Type | Purpose |
|---|---|---|
| `ck_encounters_period_start_before_end` | check constraint | Ensures `period_start_at <= period_end_at` when `period_end_at` exists |

Planned indexes:

| Name | Columns | Purpose |
|---|---|---|
| `ix_encounters_patient_id` | `patient_id` | List encounters for a patient |
| `ix_encounters_patient_period_start_at` | `patient_id`, `period_start_at` | List/order encounters for a patient by start date |

Notes:

- `period_start_at` is required because the domain `Encounter` requires `period.start`.
- `period_end_at` is optional because the domain `Period.end` is optional.
- `created_at` and `updated_at` are technical persistence metadata.
- This table should use `TimestampMixin`.

---

## Code catalog design

Observation and Condition codes will use separate catalog tables:

    observation_codes
    condition_codes

The clinical rows will reference catalog rows through:

    observations.code_id -> observation_codes.id
    conditions.code_id -> condition_codes.id

The clinical rows will not duplicate:

    code_system
    code_code
    code_display

Reason:

- code catalogs support future UI dropdowns
- code catalogs avoid repeated code data in clinical rows
- code catalogs make supported/selectable codes easier to seed and maintain
- separate catalogs are clearer than a generic code table at this project stage

A single generic `clinical_codes` table is intentionally deferred.

---

## ObservationStatus design

`ObservationStatus` is not persisted through a catalog table.

Do not create:

    observation_statuses

Instead:

    observations.status

will be stored as a string with a check constraint.

Reason:

- `ObservationStatus` is a small closed set
- it is a resource state set, not an administratively maintained terminology catalog
- the domain enum-like type remains the source of truth
- the database check constraint protects persistence integrity
- future UI should obtain allowed statuses through API/OpenAPI/metadata, not by duplicating constants manually

---

## Quantity design

`Observation.value` will be persisted as explicit columns:

    value_quantity
    value_unit

Do not store Quantity as JSON.

Reason:

- the shape is simple
- the fields are queryable
- the mapping is clear
- the database can enforce that `value_unit` exists when `value_quantity` exists

Planned constraint:

    ck_observations_value_quantity_requires_unit

---

## Reference persistence design

The domain `Reference.resource_type` is constrained to supported resource types.

Current supported values:

    Patient
    Observation
    Condition
    Encounter

However, `Observation`, `Condition`, and `Encounter` subjects currently must reference `Patient`.

Therefore, their persistence tables should use:

    patient_id

not:

    subject_resource_type
    subject_id

This keeps the schema relational and aligned with current domain rules.

Future `AuditEventRecord` may need a different representation because `AuditEvent.entity` may reference different supported resource types.

That belongs to the future AuditEvent persistence sub-issue.

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

Planned Sub-issue E migration:

    create clinical resource tables

It should create:

    observation_codes
    condition_codes
    observations
    conditions
    encounters

It should not include:

- seed data
- triggers
- mappers
- adapters
- HTTP behavior

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

The planned clinical resource migration for Sub-issue E should also be manual.

This means the migration file intentionally repeats the schema already represented in the ORM models.

The two artifacts have different responsibilities:

- ORM models represent the current desired persistence shape.
- Alembic migrations represent historical steps to move the database from one schema version to another.

Manual migrations are useful for understanding the schema, but they introduce the risk of divergence between ORM models and migration scripts.

For this reason, model tests and migration review are required.

Future work should introduce Alembic autogeneration plus manual review once the PostgreSQL workflow is ready.

---

## Persistence tests

Run all persistence tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy

Run Patient ORM model tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models/test_patient_orm_models.py

Run future Sub-issue E ORM tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models

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

- Observation code ORM model
- Condition code ORM model
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
- database trigger hardening for `updated_at`

These capabilities are intentionally deferred.

---

## Planned persistence work

Likely next Phase 3 persistence sub-issues:

1. Add Observation, Condition, and Encounter ORM models and migration.
2. Add AuditEvent ORM model and migration.
3. Add ORM/domain mappers.
4. Add SQLAlchemy adapters for application ports.
5. Wire selected persistence-backed use-cases through HTTP/dependencies.
6. Add local PostgreSQL workflow.
7. Add Alembic autogeneration workflow.
8. Add integration testing strategy for migrations and adapters.
9. Add database trigger hardening for `updated_at` consistency when justified.

The database-wide timestamp and audit metadata strategy has already been decided in ADR 0014.

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
9. Follow ADR 0014 for timestamp and audit metadata strategy.
10. Do not allow persistence schemas to silently drive domain design.
11. Do not introduce broad generic repositories until repeated adapter duplication justifies it.
12. Do not introduce database triggers before the trigger hardening backlog is executed.
13. Keep audit events separate from row timestamps.
14. Keep clinical dates separate from technical persistence timestamps.

---

## Related ADRs

Current related ADRs:

- ADR 0012: SQLAlchemy persistence foundation and mapping boundaries
- ADR 0013: Centralized runtime configuration
- ADR 0014: Database timestamp and audit metadata strategy

---

## Related backlog items

Current related backlog items:

- BACKLOG / HARDEN / P3+ / Add database triggers for `updated_at` consistency
