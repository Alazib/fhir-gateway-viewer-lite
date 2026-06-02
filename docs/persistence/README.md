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
- reusable SQLAlchemy `TimestampMixin`
- Patient ORM schema
- Patient identifier ORM schema
- Observation code catalog ORM schema
- Condition code catalog ORM schema
- Observation ORM schema
- Condition ORM schema
- Encounter ORM schema
- manual Patient migration
- manual clinical resource tables migration
- ORM metadata tests
- migration SQL rendering validation
- architecture boundary tests preventing SQLAlchemy imports in domain/application
- constrained domain `Reference.resource_type`
- ADR 0014 database timestamp and audit metadata strategy

Current clinical persistence schemas:

| Resource / table group | Status |
|---|---|
| Patient | Implemented |
| Patient identifiers | Implemented |
| Observation codes | Implemented |
| Condition codes | Implemented |
| Observation | Implemented |
| Condition | Implemented |
| Encounter | Implemented |
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
- `mixins.py`: contains reusable SQLAlchemy persistence mixins such as `TimestampMixin`.
- `models/`: contains SQLAlchemy ORM models.
- `models/patient.py`: defines Patient and Patient identifier persistence records.
- `models/observation.py`: defines Observation code catalog and Observation records.
- `models/condition.py`: defines Condition code catalog and Condition records.
- `models/encounter.py`: defines Encounter records.
- `models/__init__.py`: imports and exports all current ORM records so they are registered in `Base.metadata`.

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

Current ORM tables registered in metadata:

    patients
    patient_identifiers
    observation_codes
    condition_codes
    observations
    conditions
    encounters

Alembic uses this metadata to understand the target schema.

Important note:

SQLAlchemy registers tables in `Base.metadata` when Python imports and evaluates ORM model classes.

Alembic does not discover ORM classes by scanning folders.

For this reason, `alembic/env.py` imports the SQLAlchemy `models` package so the model modules are loaded before Alembic reads `Base.metadata`.

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
- Top-level ORM-managed tables include `created_at` and `updated_at`.
- Dependent component tables do not receive timestamps by default.
- Domain entities do not receive `created_at` or `updated_at` by default.
- HTTP APIs do not expose technical timestamps by default.
- Phase 3 uses database server defaults plus SQLAlchemy `onupdate`.
- Database triggers are deferred to future hardening.
- Reusable SQLAlchemy timestamp behavior is implemented through `TimestampMixin`.

Current mixin:

    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/mixins.py

Current class:

    TimestampMixin

Current behavior:

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

Current ORM model modules:

    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/models/patient.py
    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/models/observation.py
    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/models/condition.py
    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/models/encounter.py

Defined ORM records:

    PatientRecord
    PatientIdentifierRecord
    ObservationCodeRecord
    ObservationRecord
    ConditionCodeRecord
    ConditionRecord
    EncounterRecord

These records are persistence models.

They are not domain entities.

The domain entities remain:

    fhir_gateway.domain.entities.patient.Patient
    fhir_gateway.domain.entities.observation.Observation
    fhir_gateway.domain.entities.condition.Condition
    fhir_gateway.domain.entities.encounter.Encounter

The domain value objects remain:

    ResourceId
    Identifier
    HumanName
    Code
    Reference
    Instant
    Period
    Quantity

Future ORM records:

    AuditEventRecord

---

## Current database schema overview

Current database tables represented by SQLAlchemy metadata and Alembic migrations:

    patients
    patient_identifiers
    observation_codes
    condition_codes
    observations
    conditions
    encounters

Pending persistence table:

    audit_events

---

## ID strategy

The persistence layer uses two ID strategies.

### Domain resource IDs

Main clinical resources use string IDs because they represent domain `ResourceId` values.

Current tables using string primary keys:

    patients.id
    observations.id
    conditions.id
    encounters.id

These IDs are controlled by the application/domain layer and are not generated by the database.

Examples:

    pat-001
    obs-001
    cond-001
    enc-001

### Technical database IDs

Dependent component tables and catalog tables use integer autoincrement IDs.

Current tables using integer autoincrement primary keys:

    patient_identifiers.id
    observation_codes.id
    condition_codes.id

Reason:

- these rows are not top-level clinical resources in the current domain model
- catalog identity is naturally represented by `(system, code)`
- integer surrogate keys make foreign keys from clinical rows simpler
- dependent component rows do not need domain-visible resource IDs

Summary:

| Table | ID column | Type | Autoincrement | Reason |
|---|---:|---:|---:|---|
| `patients` | `id` | string | no | Stores domain `ResourceId.value` |
| `patient_identifiers` | `id` | integer | yes | Technical component row ID |
| `observation_codes` | `id` | integer | yes | Technical catalog row ID |
| `condition_codes` | `id` | integer | yes | Technical catalog row ID |
| `observations` | `id` | string | no | Stores domain `ResourceId.value` |
| `conditions` | `id` | string | no | Stores domain `ResourceId.value` |
| `encounters` | `id` | string | no | Stores domain `ResourceId.value` |

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

Current constraints and indexes:

| Name | Type | Purpose |
|---|---|---|
| primary key on `id` | primary key | Identifies each persisted patient resource |

The timestamp columns are persistence metadata.

They are not part of the domain `Patient` entity at this stage.

`PatientRecord` currently uses `TimestampMixin`.

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
| primary key on `id` | primary key | Identifies each persisted identifier row |
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

And from each identifier row:

    PatientIdentifierRecord
        └── patient: PatientRecord

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
8. `PatientRecord` uses `TimestampMixin`.
9. Patient ORM records must be mapped to domain entities by infrastructure mappers in a later sub-issue.
10. Application use-cases must not return ORM records.
11. SQLAlchemy must remain isolated to infrastructure.

---

## Table: `observation_codes`

The `observation_codes` table stores the catalog of supported/selectable Observation codes.

Current purpose:

    Future UI dropdowns.
    Consistent Observation code selection.
    Avoid repeated code data inside every observation row.

Current columns:

| Column | Type | Nullable | Purpose |
|---|---:|---:|---|
| `id` | integer | no | Technical primary key |
| `system` | string | no | Code system |
| `code` | string | no | Code value |
| `display` | string | yes | Human-readable display |
| `created_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `updated_at` | timezone-aware datetime | no | Technical persistence timestamp |

Current constraints and indexes:

| Name | Type | Purpose |
|---|---|---|
| primary key on `id` | primary key | Identifies each catalog row |
| `uq_observation_codes_system_code` | unique constraint | Prevents duplicate Observation codes for the same `(system, code)` |

Notes:

- This table is a top-level ORM-managed catalog table.
- It uses `TimestampMixin`.
- It does not contain seed data yet.
- The clinical identity of a code is `(system, code)`.
- The integer `id` is a persistence surrogate key used by `observations.code_id`.

---

## Table: `condition_codes`

The `condition_codes` table stores the catalog of supported/selectable Condition codes.

Current purpose:

    Future UI dropdowns.
    Consistent Condition code selection.
    Avoid repeated code data inside every condition row.

Current columns:

| Column | Type | Nullable | Purpose |
|---|---:|---:|---|
| `id` | integer | no | Technical primary key |
| `system` | string | no | Code system |
| `code` | string | no | Code value |
| `display` | string | yes | Human-readable display |
| `created_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `updated_at` | timezone-aware datetime | no | Technical persistence timestamp |

Current constraints and indexes:

| Name | Type | Purpose |
|---|---|---|
| primary key on `id` | primary key | Identifies each catalog row |
| `uq_condition_codes_system_code` | unique constraint | Prevents duplicate Condition codes for the same `(system, code)` |

Notes:

- This table is a top-level ORM-managed catalog table.
- It uses `TimestampMixin`.
- It does not contain seed data yet.
- The clinical identity of a code is `(system, code)`.
- The integer `id` is a persistence surrogate key used by `conditions.code_id`.

---

## Table: `observations`

The `observations` table stores the persistence representation of the domain `Observation` resource.

Current columns:

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

Current foreign keys:

| Column | References | Delete behavior |
|---|---|---|
| `patient_id` | `patients.id` | `ON DELETE CASCADE` |
| `code_id` | `observation_codes.id` | restrict/no cascade |

Current constraints:

| Name | Type | Purpose |
|---|---|---|
| primary key on `id` | primary key | Identifies each persisted Observation resource |
| `ck_observations_status_allowed` | check constraint | Ensures status is one of the allowed `ObservationStatus` values |
| `ck_observations_value_quantity_requires_unit` | check constraint | Ensures `value_unit` is present when `value_quantity` is present |

Current indexes:

| Name | Columns | Purpose |
|---|---|---|
| `ix_observations_patient_code` | `patient_id`, `code_id` | List/filter observations for a patient by code |
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
- `code_id` does not cascade-delete observations when a catalog row is deleted.
- This table uses `TimestampMixin`.
- The simple `patient_id` index is intentionally not present; current query patterns are covered by composite indexes starting with `patient_id`.

---

## Table: `conditions`

The `conditions` table stores the persistence representation of the domain `Condition` resource.

Current columns:

| Column | Type | Nullable | Purpose |
|---|---:|---:|---|
| `id` | string | no | Stores `ResourceId.value`; primary key |
| `patient_id` | string | no | Foreign key to `patients.id` |
| `code_id` | integer | no | Foreign key to `condition_codes.id` |
| `recorded_at` | timezone-aware datetime | yes | Clinical recorded datetime |
| `created_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `updated_at` | timezone-aware datetime | no | Technical persistence timestamp |

Current foreign keys:

| Column | References | Delete behavior |
|---|---|---|
| `patient_id` | `patients.id` | `ON DELETE CASCADE` |
| `code_id` | `condition_codes.id` | restrict/no cascade |

Current constraints:

| Name | Type | Purpose |
|---|---|---|
| primary key on `id` | primary key | Identifies each persisted Condition resource |

Current indexes:

| Name | Columns | Purpose |
|---|---|---|
| `ix_conditions_patient_code` | `patient_id`, `code_id` | List/filter conditions for a patient by code |

Notes:

- `recorded_at` is nullable because `Condition.recorded_date` is optional in the domain.
- `created_at` and `updated_at` are technical persistence metadata.
- `code_id` does not cascade-delete conditions when a catalog row is deleted.
- This table uses `TimestampMixin`.
- The simple `patient_id` index is intentionally not present; the composite index starts with `patient_id`.

---

## Table: `encounters`

The `encounters` table stores the persistence representation of the domain `Encounter` resource.

Current columns:

| Column | Type | Nullable | Purpose |
|---|---:|---:|---|
| `id` | string | no | Stores `ResourceId.value`; primary key |
| `patient_id` | string | no | Foreign key to `patients.id` |
| `period_start_at` | timezone-aware datetime | no | Clinical encounter period start |
| `period_end_at` | timezone-aware datetime | yes | Clinical encounter period end |
| `created_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `updated_at` | timezone-aware datetime | no | Technical persistence timestamp |

Current foreign keys:

| Column | References | Delete behavior |
|---|---|---|
| `patient_id` | `patients.id` | `ON DELETE CASCADE` |

Current constraints:

| Name | Type | Purpose |
|---|---|---|
| primary key on `id` | primary key | Identifies each persisted Encounter resource |
| `ck_encounters_period_start_before_end` | check constraint | Ensures `period_start_at <= period_end_at` when `period_end_at` exists |

Current indexes:

| Name | Columns | Purpose |
|---|---|---|
| `ix_encounters_patient_period_start_at` | `patient_id`, `period_start_at` | List/order encounters for a patient by start date |

Notes:

- `period_start_at` is required because the domain `Encounter` requires `Period.start`.
- `period_end_at` is optional because the domain `Period.end` is optional.
- `created_at` and `updated_at` are technical persistence metadata.
- This table uses `TimestampMixin`.
- The simple `patient_id` index is intentionally not present; the composite index starts with `patient_id`.

---

## Code catalog design

Observation and Condition codes use separate catalog tables:

    observation_codes
    condition_codes

The clinical rows reference catalog rows through:

    observations.code_id -> observation_codes.id
    conditions.code_id -> condition_codes.id

The clinical rows do not duplicate:

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

is stored as a string with a check constraint.

Reason:

- `ObservationStatus` is a small closed set
- it is a resource state set, not an administratively maintained terminology catalog
- the domain enum-like type remains the application source of truth
- the database check constraint protects persistence integrity
- future UI should obtain allowed statuses through API/OpenAPI/metadata, not by duplicating constants manually

Current persisted allowed values:

    registered
    preliminary
    final
    amended
    corrected
    cancelled
    entered-in-error
    unknown

Important migration note:

The Alembic migration freezes these values deliberately.

Migrations are historical schema steps and should not import the live domain enum directly.

If the domain enum changes later, a new migration should update the database check constraint.

---

## Quantity design

`Observation.value` is persisted as explicit columns:

    value_quantity
    value_unit

Do not store Quantity as JSON.

Reason:

- the shape is simple
- the fields are queryable
- the mapping is clear
- the database can enforce that `value_unit` exists when `value_quantity` exists

Current constraint:

    ck_observations_value_quantity_requires_unit

Rule:

    value_quantity IS NULL OR value_unit IS NOT NULL

This mirrors the current domain rule that a quantity value requires a unit.

---

## Reference persistence design

The domain `Reference.resource_type` is constrained to supported resource types.

Current supported values:

    Patient
    Observation
    Condition
    Encounter

However, `Observation`, `Condition`, and `Encounter` subjects currently must reference `Patient`.

Therefore, their persistence tables use:

    patient_id

not:

    subject_resource_type
    subject_id

This keeps the schema relational and aligned with current domain rules.

Future `AuditEventRecord` may need a different representation because `AuditEvent.entity` may reference different supported resource types.

That belongs to the future AuditEvent persistence sub-issue.

---

## Index strategy

The current schema avoids simple `patient_id` indexes when a composite index already starts with `patient_id`.

Current composite indexes:

    ix_observations_patient_code
    ix_observations_patient_effective_at
    ix_conditions_patient_code
    ix_encounters_patient_period_start_at

Reason:

- these indexes support the expected query patterns
- their first column is `patient_id`
- they can support many patient-scoped lookups
- avoiding redundant simple indexes reduces write overhead and storage
- index additions should remain tied to concrete query patterns

Future index changes should be guided by actual adapter queries and, eventually, database query plans.

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

Current migration chain:

    <base>
        ↓
    f97f9d019499_create_patient_tables
        ↓
    ab48a83daad7_add_clinical_resource_tables

The Patient migration creates:

    patients
    patient_identifiers

It also creates:

    uq_patient_identifiers_patient_system_value
    ix_patient_identifiers_system_value

The clinical resource migration creates:

    observation_codes
    condition_codes
    observations
    conditions
    encounters

It also creates:

    uq_observation_codes_system_code
    uq_condition_codes_system_code
    ck_observations_status_allowed
    ck_observations_value_quantity_requires_unit
    ck_encounters_period_start_before_end
    ix_observations_patient_code
    ix_observations_patient_effective_at
    ix_conditions_patient_code
    ix_encounters_patient_period_start_at

The migrations do not include:

- seed data
- triggers
- mappers
- adapters
- HTTP behavior

The migrations were created manually to make the schema explicit and reviewable.

Alembic autogeneration is intentionally deferred until the project has:

- a local PostgreSQL workflow
- a clearer migration review routine
- integration tests around migrations/adapters

---

## Safe Alembic inspection commands

Show migration history:

    pipenv run alembic history --verbose

Show current heads:

    pipenv run alembic heads --verbose

Render SQL from the current patient migration to the latest migration:

    pipenv run alembic upgrade f97f9d019499:head --sql

Render SQL from base to the latest migration:

    pipenv run alembic upgrade base:head --sql

Render SQL for downgrading the clinical resource migration:

    pipenv run alembic downgrade ab48a83daad7:f97f9d019499 --sql

Render SQL without applying migrations:

    pipenv run alembic upgrade head --sql

The `--sql` command prints the SQL that Alembic would execute without applying it to the database.

Do not run database migrations yet unless a local PostgreSQL database has been created and configured.

Do not run this yet unless PostgreSQL is available and configured:

    pipenv run alembic upgrade head

---

## Manual migration note

The current migrations were created manually.

This means the migration files intentionally repeat the schema already represented in the ORM models.

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

Run all ORM model tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models

Run Patient ORM model tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models/test_patient_orm_models.py

Run code catalog ORM model tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models/test_code_catalog_orm_models.py

Run clinical resource ORM model tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models/test_clinical_resource_orm_models.py

Run model package registration tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models/test_models_package_registration.py

Run architecture boundary tests:

    pipenv run pytest tests/unit/architecture

Run full test suite:

    pipenv run pytest

Current validated state after Sub-issue E:

    224 tests passing

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

1. Add AuditEvent ORM model and migration.
2. Add ORM/domain mappers.
3. Add SQLAlchemy adapters for application ports.
4. Wire selected persistence-backed use-cases through HTTP/dependencies.
5. Add local PostgreSQL workflow.
6. Add Alembic autogeneration workflow.
7. Add integration testing strategy for migrations and adapters.
8. Add seed data strategy.
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
15. Avoid redundant indexes unless query patterns justify them.

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
