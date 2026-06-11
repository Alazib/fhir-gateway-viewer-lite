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
- reusable SQLAlchemy `LogicalDeletionMixin`
- Patient ORM schema
- Patient identifier ORM schema
- Observation code catalog ORM schema
- Condition code catalog ORM schema
- Observation ORM schema
- Condition ORM schema
- Encounter ORM schema
- logical deletion metadata for top-level clinical resources
- AuditEvent ORM schema
- manual Patient migration
- manual clinical resource tables migration
- manual logical deletion metadata migration
- manual AuditEvent table migration
- ORM metadata tests
- migration SQL rendering validation
- architecture boundary tests preventing SQLAlchemy imports in domain/application
- constrained domain `Reference.resource_type`
- ADR 0014 database timestamp and audit metadata strategy
- ADR 0015 AuditEvent persistence strategy
- ADR 0016 clinical resource logical deletion strategy

Current clinical and audit persistence schemas:

| Resource / table group | Status |
|---|---|
| Patient | Implemented |
| Patient identifiers | Implemented |
| Observation codes | Implemented |
| Condition codes | Implemented |
| Observation | Implemented |
| Condition | Implemented |
| Encounter | Implemented |
| Logical deletion metadata | Implemented |
| AuditEvent | Implemented |

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
- logical deletion strategy
- audit event persistence strategy
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
            ├── audit_event.py
            ├── condition.py
            ├── encounter.py
            ├── observation.py
            └── patient.py

Responsibilities:

- `base.py`: defines the SQLAlchemy declarative `Base`.
- `database.py`: provides helpers to create SQLAlchemy engines and session factories.
- `mixins.py`: contains reusable SQLAlchemy persistence mixins.
- `models/`: contains SQLAlchemy ORM models.
- `models/audit_event.py`: defines AuditEvent persistence records.
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

Current ORM tables registered in metadata:

    patients
    patient_identifiers
    observation_codes
    condition_codes
    observations
    conditions
    encounters
    audit_events

Alembic uses this metadata to understand the target schema.

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
- Top-level clinical ORM-managed tables include `created_at` and `updated_at`.
- Dependent component tables do not receive timestamps by default.
- Domain entities do not receive `created_at` or `updated_at` by default.
- HTTP APIs do not expose technical timestamps by default.
- Phase 3 uses database server defaults plus SQLAlchemy `onupdate`.
- Database triggers are deferred to future hardening.
- Reusable SQLAlchemy timestamp behavior is implemented through `TimestampMixin`.

Current mixin:

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

Important AuditEvent exception:

    audit_events.created_at exists
    audit_events.updated_at does not exist

Reason:

Audit events are append-oriented records.

This exception is defined in:

    ADR 0015: AuditEvent persistence strategy

---

## Logical deletion strategy

Logical deletion behavior is defined by:

    ADR 0016: Clinical resource logical deletion strategy

Top-level clinical resources use:

    deleted_at

as a nullable logical deletion marker.

Meaning:

    deleted_at IS NULL
        resource is not logically deleted

    deleted_at IS NOT NULL
        resource is logically deleted

Current mixin:

    LogicalDeletionMixin

Current behavior:

    deleted_at:
        DateTime(timezone=True)
        nullable=True

`deleted_at` has no server default and no automatic `onupdate`.

Reason:

- new resources must not be born deleted
- ordinary updates must not automatically delete resources
- `deleted_at` is set only by explicit logical deletion behavior

Affected tables:

- `patients`
- `observations`
- `conditions`
- `encounters`

Unaffected tables:

- `patient_identifiers`
- `observation_codes`
- `condition_codes`
- `audit_events`

No indexes involving `deleted_at` are introduced at this stage.

Future adapters must filter ordinary reads with:

    deleted_at IS NULL

---

## AuditEvent persistence strategy

AuditEvent persistence behavior is defined by:

    ADR 0015: AuditEvent persistence strategy

Audit events are persisted in:

    audit_events

Audit events are append-oriented historical records.

They are not ordinary clinical resources.

They do not use:

    TimestampMixin
    LogicalDeletionMixin

The table includes:

    created_at

but does not include:

    updated_at
    deleted_at

Reason:

- `created_at` records when the audit row was inserted
- `recorded_at` records when the audited action happened
- `updated_at` would imply ordinary mutable row lifecycle
- `deleted_at` would imply ordinary clinical-resource logical deletion semantics
- audit retention, redaction, purge, and tamper-evidence require separate decisions

Audit events reference audited resources using:

    entity_resource_type
    entity_id

not foreign keys.

Reason:

- `AuditEvent.entity` may refer to different resource types
- a single FK cannot point to multiple target tables
- multiple nullable FKs would be heavier and more fragile
- audit records should survive ordinary logical deletion and possible future purge workflows

Current supported entity resource types:

    Patient
    Observation
    Condition
    Encounter

Current supported actions:

    read
    search
    export

Future write-side actions such as:

    create
    update
    delete

are deferred to:

    BACKLOG / EXPAND / P3+ / Extend AuditAction for clinical write operations

Entity-based audit lookup index is deferred to:

    BACKLOG / EXPAND / P3+ / Add entity-based audit event lookup index

---

## Technical timestamps vs clinical dates

Technical timestamps describe persistence operations in this application's database.

Examples:

    created_at
    updated_at
    deleted_at

Clinical dates describe the domain meaning of a clinical resource.

Examples:

    Observation.effective
    Condition.recorded_date
    Encounter.period
    AuditEvent.recorded

Example distinction:

    observations.effective_at = 2026-05-20 08:30
    observations.created_at = 2026-05-26 12:00
    observations.deleted_at = NULL

Meaning:

    The observation was clinically effective on May 20.
    The observation row was inserted into this database on May 26.
    The observation is not logically deleted.

Audit example:

    audit_events.recorded_at = 2026-06-04 10:00
    audit_events.created_at = 2026-06-04 10:00:02

Meaning:

    The audited action happened at 10:00.
    The audit row was inserted into this database at 10:00:02.

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
    deleted_at

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

    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/models/audit_event.py
    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/models/patient.py
    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/models/observation.py
    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/models/condition.py
    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/models/encounter.py

Defined ORM records:

    AuditEventRecord
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

    fhir_gateway.domain.entities.audit_event.AuditEvent
    fhir_gateway.domain.entities.patient.Patient
    fhir_gateway.domain.entities.observation.Observation
    fhir_gateway.domain.entities.condition.Condition
    fhir_gateway.domain.entities.encounter.Encounter

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
    audit_events

---

## ID strategy

The persistence layer uses two ID strategies.

### Domain resource IDs

Main clinical resources and audit events use string IDs because they represent domain `ResourceId` values.

Current tables using string primary keys:

    patients.id
    observations.id
    conditions.id
    encounters.id
    audit_events.id

These IDs are controlled by the application/domain layer and are not generated by the database.

Examples:

    pat-001
    obs-001
    cond-001
    enc-001
    audit-001

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
|---|---|---|---|---|
| `patients` | `id` | string | no | Stores domain `ResourceId.value` |
| `patient_identifiers` | `id` | integer | yes | Technical component row ID |
| `observation_codes` | `id` | integer | yes | Technical catalog row ID |
| `condition_codes` | `id` | integer | yes | Technical catalog row ID |
| `observations` | `id` | string | no | Stores domain `ResourceId.value` |
| `conditions` | `id` | string | no | Stores domain `ResourceId.value` |
| `encounters` | `id` | string | no | Stores domain `ResourceId.value` |
| `audit_events` | `id` | string | no | Stores domain `ResourceId.value` |

---

## Table: `patients`

The `patients` table stores the persistence representation of the domain `Patient` root resource.

Current columns:

| Column | Type | Nullable | Purpose |
|---|---|---|---|
| `id` | string | no | Stores `ResourceId.value`; primary key |
| `name_text` | string | yes | Stores `HumanName.text` |
| `name_family` | string | yes | Stores `HumanName.family` |
| `name_given` | JSON | yes | Stores ordered `HumanName.given` values |
| `created_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `updated_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `deleted_at` | timezone-aware datetime | yes | Logical deletion marker |

Current constraints and indexes:

| Name | Type | Purpose |
|---|---|---|
| primary key on `id` | primary key | Identifies each persisted patient resource |

`PatientRecord` currently uses:

- `TimestampMixin`
- `LogicalDeletionMixin`

The timestamp columns and logical deletion column are persistence metadata.

They are not part of the domain `Patient` entity at this stage.

---

## Table: `patient_identifiers`

The `patient_identifiers` table stores the persistence representation of `Patient.identifiers`.

Current columns:

| Column | Type | Nullable | Purpose |
|---|---|---|---|
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

According to ADR 0016, this dependent component table does not receive `deleted_at` by default.

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

## Table: `observation_codes`

The `observation_codes` table stores the catalog of supported/selectable Observation codes.

Current columns:

| Column | Type | Nullable | Purpose |
|---|---|---|---|
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
- It does not use `LogicalDeletionMixin`.
- It does not contain seed data yet.
- The clinical identity of a code is `(system, code)`.
- The integer `id` is a persistence surrogate key used by `observations.code_id`.

---

## Table: `condition_codes`

The `condition_codes` table stores the catalog of supported/selectable Condition codes.

Current columns:

| Column | Type | Nullable | Purpose |
|---|---|---|---|
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
- It does not use `LogicalDeletionMixin`.
- It does not contain seed data yet.
- The clinical identity of a code is `(system, code)`.
- The integer `id` is a persistence surrogate key used by `conditions.code_id`.

---

## Table: `observations`

The `observations` table stores the persistence representation of the domain `Observation` resource.

Current columns:

| Column | Type | Nullable | Purpose |
|---|---|---|---|
| `id` | string | no | Stores `ResourceId.value`; primary key |
| `patient_id` | string | no | Foreign key to `patients.id` |
| `status` | string | no | Observation status |
| `code_id` | integer | no | Foreign key to `observation_codes.id` |
| `effective_at` | timezone-aware datetime | no | Clinical effective datetime |
| `value_quantity` | float | yes | Quantity numeric value |
| `value_unit` | string | yes | Quantity unit |
| `created_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `updated_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `deleted_at` | timezone-aware datetime | yes | Logical deletion marker |

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
- `created_at`, `updated_at`, and `deleted_at` are technical/application persistence metadata.
- `code_id` does not cascade-delete observations when a catalog row is deleted.
- This table uses `TimestampMixin`.
- This table uses `LogicalDeletionMixin`.
- The simple `patient_id` index is intentionally not present; current query patterns are covered by composite indexes starting with `patient_id`.
- No index involving `deleted_at` exists yet.

---

## Table: `conditions`

The `conditions` table stores the persistence representation of the domain `Condition` resource.

Current columns:

| Column | Type | Nullable | Purpose |
|---|---|---|---|
| `id` | string | no | Stores `ResourceId.value`; primary key |
| `patient_id` | string | no | Foreign key to `patients.id` |
| `code_id` | integer | no | Foreign key to `condition_codes.id` |
| `recorded_at` | timezone-aware datetime | yes | Clinical recorded datetime |
| `created_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `updated_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `deleted_at` | timezone-aware datetime | yes | Logical deletion marker |

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
- `created_at`, `updated_at`, and `deleted_at` are technical/application persistence metadata.
- `code_id` does not cascade-delete conditions when a catalog row is deleted.
- This table uses `TimestampMixin`.
- This table uses `LogicalDeletionMixin`.
- The simple `patient_id` index is intentionally not present; the composite index starts with `patient_id`.
- No index involving `deleted_at` exists yet.

---

## Table: `encounters`

The `encounters` table stores the persistence representation of the domain `Encounter` resource.

Current columns:

| Column | Type | Nullable | Purpose |
|---|---|---|---|
| `id` | string | no | Stores `ResourceId.value`; primary key |
| `patient_id` | string | no | Foreign key to `patients.id` |
| `period_start_at` | timezone-aware datetime | no | Clinical encounter period start |
| `period_end_at` | timezone-aware datetime | yes | Clinical encounter period end |
| `created_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `updated_at` | timezone-aware datetime | no | Technical persistence timestamp |
| `deleted_at` | timezone-aware datetime | yes | Logical deletion marker |

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
- `created_at`, `updated_at`, and `deleted_at` are technical/application persistence metadata.
- This table uses `TimestampMixin`.
- This table uses `LogicalDeletionMixin`.
- The simple `patient_id` index is intentionally not present; the composite index starts with `patient_id`.
- No index involving `deleted_at` exists yet.

---

## Table: `audit_events`

The `audit_events` table stores the persistence representation of the domain `AuditEvent` resource.

Current columns:

| Column | Type | Nullable | Purpose |
|---|---|---|---|
| `id` | string | no | Stores `ResourceId.value`; primary key |
| `recorded_at` | timezone-aware datetime | no | Audit/domain timestamp; maps `AuditEvent.recorded` |
| `agent` | string | no | Actor/system/client string supplied by trusted runtime context |
| `action` | string | no | Audit action value |
| `entity_resource_type` | string | no | Referenced entity resource type |
| `entity_id` | string | no | Referenced entity resource id |
| `created_at` | timezone-aware datetime | no | Technical insertion timestamp |

Forbidden columns:

| Column | Reason |
|---|---|
| `updated_at` | Audit events are append-oriented records |
| `deleted_at` | Audit events do not follow ordinary clinical logical deletion semantics |

Current constraints:

| Name | Type | Purpose |
|---|---|---|
| primary key on `id` | primary key | Identifies each persisted AuditEvent |
| `ck_audit_events_action_allowed` | check constraint | Restricts action to current `AuditAction` values |
| `ck_audit_events_entity_resource_type_allowed` | check constraint | Restricts entity resource type to supported reference resource types |
| `ck_audit_events_agent_not_empty` | check constraint | Prevents blank agent strings |

Current indexes:

| Name | Columns | Purpose |
|---|---|---|
| `ix_audit_events_recorded_at` | `recorded_at` | Supports listing recent audit events |

Current allowed actions:

    read
    search
    export

Current allowed entity resource types:

    Patient
    Observation
    Condition
    Encounter

Notes:

- `recorded_at` is the audit event timestamp.
- `created_at` is the technical database insertion timestamp.
- `agent` is required but not modeled as a foreign key, enum, or catalog.
- `agent` must come from trusted runtime context in future audit write behavior.
- `entity_resource_type` and `entity_id` form a logical polymorphic reference.
- `entity_id` has no foreign key.
- `audit_events` does not use `TimestampMixin`.
- `audit_events` does not use `LogicalDeletionMixin`.
- No entity lookup index exists yet.

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

Catalog lifecycle is not the same as clinical resource logical deletion.

Future catalog lifecycle may use fields such as:

    is_selectable
    retired_at
    valid_from
    valid_to

That is outside the current persistence slice.

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

## AuditAction design

`AuditAction` is not persisted through a catalog table.

Do not create:

    audit_actions

Instead:

    audit_events.action

is stored as a string with a check constraint.

Reason:

- `AuditAction` is currently a small closed set
- current actions are enough for read-side and export-side use-cases
- the domain enum remains the application source of truth
- the database check constraint protects persistence integrity

Current persisted allowed values:

    read
    search
    export

Important migration note:

The Alembic migration freezes these values deliberately.

Migrations are historical schema steps and should not import the live domain enum directly.

If the domain enum changes later, a new migration should update the database check constraint.

Future write-side actions such as:

    create
    update
    delete

are deferred to:

    BACKLOG / EXPAND / P3+ / Extend AuditAction for clinical write operations

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

`Observation`, `Condition`, and `Encounter` subjects currently must reference `Patient`.

Therefore, their persistence tables use:

    patient_id

not:

    subject_resource_type
    subject_id

This keeps the schema relational and aligned with current domain rules.

`AuditEvent.entity` is different because it may reference multiple supported resource types.

Therefore, `audit_events` uses:

    entity_resource_type
    entity_id

not:

    patient_id
    observation_id
    condition_id
    encounter_id

and not a foreign key.

---

## Index strategy

The current schema avoids simple `patient_id` indexes when a composite index already starts with `patient_id`.

Current clinical composite indexes:

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

Current audit index:

    ix_audit_events_recorded_at

Reason:

- supports listing recent audit events
- aligns with current `ListAuditEventsUseCase`
- current use-case orders by recent audit time

No indexes involving `deleted_at` are introduced yet.

No audit entity lookup index is introduced yet.

Deferred audit entity lookup index:

    ix_audit_events_entity(entity_resource_type, entity_id)

Tracked by:

    BACKLOG / EXPAND / P3+ / Add entity-based audit event lookup index

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
        ↓
    d4e8f2a1c9b7_add_logical_deletion_columns_to_clinical_resources
        ↓
    a6f3c9d2e1b8_add_audit_event_table

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

The logical deletion migration adds:

    patients.deleted_at
    observations.deleted_at
    conditions.deleted_at
    encounters.deleted_at

The AuditEvent migration creates:

    audit_events

It also creates:

    ck_audit_events_action_allowed
    ck_audit_events_entity_resource_type_allowed
    ck_audit_events_agent_not_empty
    ix_audit_events_recorded_at

The AuditEvent migration does not add:

- `updated_at`
- `deleted_at`
- entity lookup index
- foreign keys to clinical tables
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

Render SQL from the current logical deletion schema to the AuditEvent migration:

    pipenv run alembic upgrade d4e8f2a1c9b7:head --sql

Render SQL from base to head:

    pipenv run alembic upgrade base:head --sql

Render downgrade from AuditEvent migration to previous migration:

    pipenv run alembic downgrade a6f3c9d2e1b8:d4e8f2a1c9b7 --sql

Do not run migrations against PostgreSQL until the local PostgreSQL workflow has been explicitly configured.

---

## Testing

Run persistence tests from:

    apps/api

Run all persistence tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy

Run ORM model tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models

Run mixin tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/test_mixins.py

Run AuditEvent ORM model tests:

    pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models/test_audit_event_orm_models.py

Run architecture boundary tests:

    pipenv run pytest tests/unit/architecture

Run the full backend test suite:

    pipenv run pytest

Current validated state:

    full test suite passing

---

## Current limitations

The persistence layer does not yet include:

- ORM/domain mappers
- SQLAlchemy adapters
- request-scoped SQLAlchemy session management
- persistence-backed HTTP endpoints
- local PostgreSQL workflow
- Alembic autogeneration workflow
- integration tests against PostgreSQL
- seed data
- logical delete/restore use-cases
- physical purge workflow
- partial indexes for logically non-deleted rows
- audit event reader adapter
- audit event writer adapter
- current-agent provider
- audit event recorder service
- audit middleware
- authentication/authorization integration
- entity-based audit filtering
- advanced audit pagination
- trigger-based `updated_at` hardening

---

## Planned persistence work

Likely next work after this persistence schema slice:

1. Add ORM/domain mappers.
2. Add SQLAlchemy adapters.
3. Wire selected persistence-backed use-cases through HTTP/dependencies.
4. Add local PostgreSQL workflow.
5. Add Alembic autogeneration workflow.
6. Add integration testing strategy.
7. Add seed data strategy.
8. Add trigger hardening if needed.
9. Add audit event reader adapter.
10. Add controlled audit event write pipeline later.

---

## Persistence design principles

1. Keep SQLAlchemy isolated to infrastructure.
2. Keep domain entities independent from ORM models.
3. Keep application ports independent from SQLAlchemy.
4. Use ORM/domain mappers at the infrastructure boundary.
5. Use Alembic for schema changes.
6. Prefer explicit manually reviewed migrations at this stage.
7. Avoid schema expansion without current use-case pressure.
8. Avoid premature generic repositories.
9. Keep routers out of persistence details.
10. Treat technical timestamps as persistence metadata.
11. Treat clinical dates as domain data.
12. Treat audit events as separate from row timestamps.
13. Use logical deletion for top-level clinical resources.
14. Hide logically deleted resources from ordinary future reads by default.
15. Do not add indexes until query patterns justify them.
16. Treat audit events as append-oriented records.
17. Do not use ordinary clinical logical deletion for audit events.
18. Do not let arbitrary user-controlled input define audit `agent`.

---

## Related ADRs

- ADR 0012: SQLAlchemy persistence foundation and mapping boundaries
- ADR 0013: Centralized runtime configuration
- ADR 0014: Database timestamp and audit metadata strategy
- ADR 0015: AuditEvent persistence strategy
- ADR 0016: Clinical resource logical deletion strategy

---

## Related backlog items

- BACKLOG / HARDEN / P3+ / Add database triggers for `updated_at` consistency
- BACKLOG / EXPAND / P3+ / Add entity-based audit event lookup index
- BACKLOG / EXPAND / P3+ / Extend AuditAction for clinical write operations
