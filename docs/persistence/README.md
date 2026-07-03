# FHIR Mini-Gateway Persistence Documentation

## Table of contents

* [1. Status](#1-status)
* [2. Purpose](#2-purpose)
* [3. Architectural boundaries](#3-architectural-boundaries)
* [4. Persistence structure](#4-persistence-structure)
* [5. Runtime database configuration](#5-runtime-database-configuration)
* [6. Engine, session factory and HTTP database dependency](#6-engine-session-factory-and-http-database-dependency)
* [7. SQLAlchemy read adapters](#7-sqlalchemy-read-adapters)
* [8. ORM/domain mapper strategy](#8-ormdomain-mapper-strategy)
* [9. Current database schema overview](#9-current-database-schema-overview)
* [10. Timestamp strategy](#10-timestamp-strategy)
* [11. Logical deletion strategy](#11-logical-deletion-strategy)
* [12. AuditEvent persistence strategy](#12-auditevent-persistence-strategy)
* [13. Technical timestamps vs clinical dates](#13-technical-timestamps-vs-clinical-dates)
* [14. Code catalog design](#14-code-catalog-design)
* [15. Reference persistence design](#15-reference-persistence-design)
* [16. Index strategy](#16-index-strategy)
* [17. Alembic migrations](#17-alembic-migrations)
* [18. Testing](#18-testing)
* [19. Current limitations](#19-current-limitations)
* [20. Planned persistence work](#20-planned-persistence-work)
* [21. Persistence design principles](#21-persistence-design-principles)
* [22. Related ADRs](#22-related-adrs)
* [23. Related backlog items](#23-related-backlog-items)

---

## 1. Status

Current persistence status: **Phase 3 / Backend foundation implemented**

Current API/security status: **Phase 4 / Security foundation in progress**

The backend currently includes:

* SQLAlchemy ORM
* Alembic
* Psycopg 3
* centralized `database_url` setting
* SQLAlchemy declarative `Base`
* database engine/session factory helpers
* request-scoped HTTP database session dependency
* application use-case dependency wiring through SQLAlchemy read adapters
* Alembic configuration
* reusable SQLAlchemy `TimestampMixin`
* reusable SQLAlchemy `LogicalDeletionMixin`
* Patient ORM schema
* Patient identifier ORM schema
* Observation code catalog ORM schema
* Condition code catalog ORM schema
* Observation ORM schema
* Condition ORM schema
* Encounter ORM schema
* logical deletion metadata for top-level clinical resources
* AuditEvent ORM schema
* ORM/domain mapper package
* Patient ORM/domain mapper
* Observation ORM/domain mapper
* Condition ORM/domain mapper
* Encounter ORM/domain mapper
* AuditEvent ORM/domain mapper
* ORM/domain mapper tests
* SQLAlchemy read adapter package
* Patient SQLAlchemy read adapter
* Observation SQLAlchemy read adapter
* Condition SQLAlchemy read adapter
* Encounter SQLAlchemy read adapter
* AuditEvent SQLAlchemy read adapter
* SQLAlchemy read adapter tests
* manual Patient migration
* manual clinical resource tables migration
* manual logical deletion metadata migration
* manual AuditEvent table migration
* ORM metadata tests
* migration SQL rendering validation
* architecture boundary tests preventing SQLAlchemy imports in domain/application
* constrained domain `Reference.resource_type`
* ADR 0014 database timestamp and audit metadata strategy
* ADR 0015 AuditEvent persistence strategy
* ADR 0016 clinical resource logical deletion strategy

Current clinical and audit persistence schemas:

| Resource / table group    | Status      |
| ------------------------- | ----------- |
| Patient                   | Implemented |
| Patient identifiers       | Implemented |
| Observation codes         | Implemented |
| Condition codes           | Implemented |
| Observation               | Implemented |
| Condition                 | Implemented |
| Encounter                 | Implemented |
| Logical deletion metadata | Implemented |
| AuditEvent                | Implemented |

SQLAlchemy read adapters have been implemented for the current application read ports.

ORM/domain mappers have been implemented for the current read-side persistence resources.

HTTP dependency wiring for database sessions, adapters and current read-side use-cases exists, but broad persistence-backed clinical HTTP endpoints are not exposed yet.

---

## 2. Purpose

This document describes the persistence layer of the `FHIR Gateway Viewer Lite` backend.

It covers:

* persistence architecture
* SQLAlchemy structure
* database engine/session configuration
* HTTP database dependency wiring
* Alembic migrations
* current ORM models
* ORM/domain mapper strategy
* SQLAlchemy read adapter strategy
* current database schema
* timestamp strategy
* logical deletion strategy
* audit event persistence strategy
* persistence design principles
* current limitations
* future persistence work

API behavior and HTTP endpoint documentation live in:

```text
docs/api/README.md
```

Security behavior lives in:

```text
docs/security/README.md
```

---

## 3. Architectural boundaries

Persistence belongs to the infrastructure layer.

The domain layer must not import:

* SQLAlchemy
* Alembic
* Psycopg
* ORM models
* database sessions
* database engine helpers

The application layer must not import:

* SQLAlchemy
* Alembic
* Psycopg
* ORM models
* database sessions
* database engine helpers

The intended dependency direction is:

```text
domain
    ↑
application
    ↑
infrastructure
```

Infrastructure may depend on domain and application.

Domain and application must not depend on infrastructure.

HTTP dependencies may compose infrastructure adapters and application use-cases at runtime, but that composition must stay at the interface boundary.

---

## 4. Persistence structure

Current structure:

```text
apps/api/src/fhir_gateway/infrastructure/persistence/
├── __init__.py
└── sqlalchemy/
    ├── __init__.py
    ├── base.py
    ├── database.py
    ├── mixins.py
    ├── adapters/
    │   ├── __init__.py
    │   ├── audit_event_reader.py
    │   ├── condition_reader.py
    │   ├── encounter_reader.py
    │   ├── observation_reader.py
    │   └── patient_reader.py
    ├── mappers/
    │   ├── __init__.py
    │   ├── audit_event.py
    │   ├── condition.py
    │   ├── encounter.py
    │   ├── observation.py
    │   └── patient.py
    └── models/
        ├── __init__.py
        ├── audit_event.py
        ├── condition.py
        ├── encounter.py
        ├── observation.py
        └── patient.py
```

Responsibilities:

* `base.py`: defines the SQLAlchemy declarative `Base`.
* `database.py`: provides helpers to create SQLAlchemy engines and session factories.
* `mixins.py`: contains reusable SQLAlchemy persistence mixins.
* `adapters/`: contains SQLAlchemy read adapters implementing application persistence ports.
* `models/`: contains SQLAlchemy ORM models.
* `mappers/`: contains SQLAlchemy ORM-to-domain mapper functions.

HTTP composition lives outside the persistence package:

```text
apps/api/src/fhir_gateway/interfaces/http/dependencies/
├── adapters.py
├── database.py
└── use_cases.py
```

---

## 5. Runtime database configuration

The database URL is defined in:

```text
apps/api/src/fhir_gateway/infrastructure/config/settings.py
```

Current setting:

| Setting        | Environment variable        | Default                                                              |
| -------------- | --------------------------- | -------------------------------------------------------------------- |
| `database_url` | `FHIR_GATEWAY_DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/fhir_gateway` |

Example PowerShell override:

```powershell
$env:FHIR_GATEWAY_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/fhir_gateway"
```

The default value is for local development only.

Production database credentials must be provided through environment variables or a future secrets management strategy.

---

## 6. Engine, session factory and HTTP database dependency

Database helpers are defined in:

```text
apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/database.py
```

Current helpers:

```text
create_database_engine(database_url)
create_session_factory(engine)
```

Current application startup flow:

```text
Settings.database_url
    -> create_database_engine(...)
        -> create_session_factory(...)
            -> app.state.session_factory
```

The HTTP layer exposes a request-scoped database session dependency:

```text
get_database_session(request)
```

Conceptual flow:

```text
FastAPI request
    -> get_database_session()
        -> session_factory()
            -> SQLAlchemy Session
                -> SQLAlchemy read adapter
                    -> application use-case
```

The session is created at the HTTP boundary and injected into adapters through dependencies.

Individual adapters do not create their own sessions.

Individual read adapters also do not commit transactions.

This keeps session lifecycle management centralized in the HTTP/interface layer.

---

## 7. SQLAlchemy read adapters

SQLAlchemy read adapters are implemented under:

```text
apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/adapters/
```

Current adapter classes:

```text
SqlAlchemyAuditEventReader
SqlAlchemyConditionReader
SqlAlchemyEncounterReader
SqlAlchemyObservationReader
SqlAlchemyPatientReader
```

Current adapter coverage:

| Adapter                       | Application port behavior                          |
| ----------------------------- | -------------------------------------------------- |
| `SqlAlchemyPatientReader`     | Reads patients by id and searches patients by text |
| `SqlAlchemyObservationReader` | Lists observations by patient and by patient/code  |
| `SqlAlchemyConditionReader`   | Lists conditions by patient                        |
| `SqlAlchemyEncounterReader`   | Lists encounters by patient                        |
| `SqlAlchemyAuditEventReader`  | Lists recent audit events                          |

These adapters are infrastructure implementations of application-layer persistence ports.

They are responsible for:

```text
building SQLAlchemy SELECT statements
applying persistence-level filters such as logical deletion
loading related ORM data required by mappers
executing queries through a SQLAlchemy Session
converting ORM records to domain entities through mapper functions
```

They must not:

```text
expose ORM records to the application layer
contain business rules that belong in domain or application services
commit transactions
create database sessions by themselves
import HTTP/FastAPI code
```

Current read adapter direction:

```text
SQLAlchemy ORM records -> ORM/domain mappers -> Domain entities
```

The reverse direction is intentionally not implemented yet:

```text
Domain entities -> SQLAlchemy ORM records
```

Reason:

The current MVP persistence flow is read-oriented.

Future write-side mapping and persistence are deferred until write-side use-cases require them.

### 7.1. Patient read adapter

Current class:

```text
SqlAlchemyPatientReader
```

Implemented application behaviors:

```text
get_by_id(patient_id: ResourceId) -> Patient | None
search_by_text(search_text: str) -> tuple[Patient, ...]
```

Search behavior currently matches patient text against:

```text
patients.id
patients.name_text
patients.name_family
patient_identifiers.system
patient_identifiers.value
```

Ordinary patient reads filter out logically deleted patients with:

```text
patients.deleted_at IS NULL
```

The adapter eager-loads patient identifiers before mapping.

Reason:

The mapper reads `PatientRecord.identifiers`.

The adapter controls loading strategy so the mapper does not accidentally trigger database queries.

### 7.2. Observation read adapter

Current class:

```text
SqlAlchemyObservationReader
```

Implemented behaviors:

```text
list_by_patient(patient_id: ResourceId) -> tuple[Observation, ...]
list_by_patient_and_code(patient_id: ResourceId, code: Code) -> tuple[Observation, ...]
```

The adapter joins:

```text
observations.code_id -> observation_codes.id
```

Reason:

`ObservationRecord` stores only `code_id`.

The domain `Observation` requires a full `Code(system, code, display)` value object.

Ordinary observation reads filter out logically deleted observations with:

```text
observations.deleted_at IS NULL
```

Current ordering:

```text
observations.effective_at ASC
observations.id ASC
```

### 7.3. Condition read adapter

Current class:

```text
SqlAlchemyConditionReader
```

Implemented behavior:

```text
list_by_patient(patient_id: ResourceId) -> tuple[Condition, ...]
```

The adapter joins:

```text
conditions.code_id -> condition_codes.id
```

Ordinary condition reads filter out logically deleted conditions with:

```text
conditions.deleted_at IS NULL
```

Current ordering:

```text
conditions.recorded_at ASC
conditions.id ASC
```

### 7.4. Encounter read adapter

Current class:

```text
SqlAlchemyEncounterReader
```

Implemented behavior:

```text
list_by_patient(patient_id: ResourceId) -> tuple[Encounter, ...]
```

No catalog join is required.

Ordinary encounter reads filter out logically deleted encounters with:

```text
encounters.deleted_at IS NULL
```

Current ordering:

```text
encounters.period_start_at ASC
encounters.id ASC
```

### 7.5. AuditEvent read adapter

Current class:

```text
SqlAlchemyAuditEventReader
```

Implemented behavior:

```text
list_recent(limit: int) -> tuple[AuditEvent, ...]
```

AuditEvent records are append-oriented.

They do not use:

```text
LogicalDeletionMixin
deleted_at
```

Therefore, the audit event reader does not filter by logical deletion.

Current ordering:

```text
audit_events.recorded_at DESC
audit_events.id ASC
```

---

## 8. ORM/domain mapper strategy

ORM/domain mappers are implemented under:

```text
apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/mappers/
```

Current mapper functions:

```text
audit_event_record_to_domain
condition_record_to_domain
encounter_record_to_domain
observation_record_to_domain
patient_record_to_domain
```

These mappers translate already-loaded SQLAlchemy ORM records into domain entities.

Current mapping direction:

```text
ORM record -> Domain entity
```

The reverse direction is intentionally not implemented yet:

```text
Domain entity -> ORM record
```

Reason:

The current MVP persistence flow is read-oriented.

Future write-side mapping is deferred until future write-side use-cases require it.

### 8.1. Mapper responsibility

Mappers are responsible for transforming persistence records into domain objects.

Examples:

```text
PatientRecord -> Patient
ObservationRecord + ObservationCodeRecord -> Observation
ConditionRecord + ConditionCodeRecord -> Condition
EncounterRecord -> Encounter
AuditEventRecord -> AuditEvent
```

Mappers construct real domain entities and value objects.

Examples:

```text
ResourceId
Identifier
HumanName
Code
Reference
Instant
Period
Quantity
Patient
Observation
Condition
Encounter
AuditEvent
```

This means mapper output passes through domain validation.

If persisted data is incompatible with domain invariants, mapping should fail rather than silently returning invalid domain objects.

### 8.2. Mapper non-responsibilities

Mappers must not:

```text
open database sessions
execute SQL queries
perform joins
perform lazy loading intentionally
filter logically deleted records
decide query visibility
expose technical persistence metadata as domain fields
return ORM records
return dictionaries instead of domain entities
```

Querying and loading are adapter responsibilities.

Mapping is transformation responsibility.

### 8.3. Logical deletion and mappers

Top-level clinical ORM records may include:

```text
deleted_at
```

Current affected records:

```text
PatientRecord
ObservationRecord
ConditionRecord
EncounterRecord
```

Mappers do not filter by:

```text
deleted_at IS NULL
```

Reason:

Logical deletion is a query visibility concern.

SQLAlchemy adapters filter ordinary reads with:

```text
deleted_at IS NULL
```

The mapper assumes that if a record is passed to it, it should attempt to map it.

### 8.4. Technical metadata and mappers

Current technical persistence metadata includes:

```text
created_at
updated_at
deleted_at
```

Current domain entities do not expose these fields by default.

Therefore, ORM/domain mappers ignore these fields.

Examples:

```text
PatientRecord.created_at      is not mapped to Patient
PatientRecord.updated_at      is not mapped to Patient
PatientRecord.deleted_at      is not mapped to Patient
ObservationRecord.deleted_at  is not mapped to Observation
AuditEventRecord.created_at   is not mapped to AuditEvent
```

AuditEvent-specific distinction:

```text
AuditEventRecord.recorded_at -> AuditEvent.recorded
AuditEventRecord.created_at  -> ignored technical insert timestamp
```

Reason:

`recorded_at` describes when the audited action happened.

`created_at` describes when the audit row was inserted into this database.

---

## 9. Current database schema overview

Current database tables represented by SQLAlchemy metadata and Alembic migrations:

```text
patients
patient_identifiers
observation_codes
condition_codes
observations
conditions
encounters
audit_events
```

### 9.1. ID strategy

The persistence layer uses two ID strategies.

Domain resource IDs:

```text
patients.id
observations.id
conditions.id
encounters.id
audit_events.id
```

These are string IDs controlled by the application/domain layer.

Examples:

```text
pat-001
obs-001
cond-001
enc-001
audit-001
```

Technical database IDs:

```text
patient_identifiers.id
observation_codes.id
condition_codes.id
```

These are integer autoincrement IDs.

Reason:

* dependent component rows and catalog rows are not top-level clinical resources
* catalog identity is naturally represented by `(system, code)`
* integer surrogate keys make foreign keys from clinical rows simpler

### 9.2. Main table summary

| Table                 | Purpose                                         |
| --------------------- | ----------------------------------------------- |
| `patients`            | Stores persisted Patient root resources         |
| `patient_identifiers` | Stores Patient identifiers as dependent records |
| `observation_codes`   | Stores supported/selectable Observation codes   |
| `condition_codes`     | Stores supported/selectable Condition codes     |
| `observations`        | Stores persisted Observation resources          |
| `conditions`          | Stores persisted Condition resources            |
| `encounters`          | Stores persisted Encounter resources            |
| `audit_events`        | Stores append-oriented AuditEvent records       |

### 9.3. Main clinical relationships

```text
patients 1 -> N patient_identifiers
patients 1 -> N observations
patients 1 -> N conditions
patients 1 -> N encounters

observation_codes 1 -> N observations
condition_codes   1 -> N conditions
```

Audit events use a logical polymorphic reference:

```text
audit_events.entity_resource_type
audit_events.entity_id
```

They do not use foreign keys to clinical tables.

---

## 10. Timestamp strategy

Timestamp behavior is defined by:

```text
ADR 0014: Database timestamp and audit metadata strategy
```

Selected convention:

* `created_at` and `updated_at` are technical persistence metadata.
* They are not clinical dates.
* They are not audit events.
* Top-level clinical ORM-managed tables include `created_at` and `updated_at`.
* Dependent component tables do not receive timestamps by default.
* Domain entities do not receive `created_at` or `updated_at` by default.
* HTTP APIs do not expose technical timestamps by default.
* Phase 3 uses database server defaults plus SQLAlchemy `onupdate`.
* Database triggers are deferred to future hardening.
* Reusable SQLAlchemy timestamp behavior is implemented through `TimestampMixin`.

Current mixin:

```text
TimestampMixin
```

Current behavior:

```text
created_at:
    DateTime(timezone=True)
    server_default=func.now()
    nullable=False

updated_at:
    DateTime(timezone=True)
    server_default=func.now()
    onupdate=func.now()
    nullable=False
```

Known limitation:

```text
Direct SQL updates outside SQLAlchemy may not update updated_at.
```

Trigger-based hardening is tracked separately:

```text
BACKLOG / POST-MVP / HARDEN / Add database triggers for updated_at consistency
```

Important AuditEvent exception:

```text
audit_events.created_at exists
audit_events.updated_at does not exist
```

Reason:

Audit events are append-oriented records.

---

## 11. Logical deletion strategy

Logical deletion behavior is defined by:

```text
ADR 0016: Clinical resource logical deletion strategy
```

Top-level clinical resources use:

```text
deleted_at
```

as a nullable logical deletion marker.

Meaning:

```text
deleted_at IS NULL
    resource is not logically deleted

deleted_at IS NOT NULL
    resource is logically deleted
```

Current mixin:

```text
LogicalDeletionMixin
```

Affected tables:

* `patients`
* `observations`
* `conditions`
* `encounters`

Unaffected tables:

* `patient_identifiers`
* `observation_codes`
* `condition_codes`
* `audit_events`

Current clinical SQLAlchemy read adapters filter ordinary reads with:

```text
deleted_at IS NULL
```

AuditEvent reads do not apply this filter because audit events do not use logical deletion.

---

## 12. AuditEvent persistence strategy

AuditEvent persistence behavior is defined by:

```text
ADR 0015: AuditEvent persistence strategy
```

Audit events are persisted in:

```text
audit_events
```

Audit events are append-oriented historical records.

They are not ordinary clinical resources.

They do not use:

```text
TimestampMixin
LogicalDeletionMixin
```

The table includes:

```text
created_at
```

but does not include:

```text
updated_at
deleted_at
```

Reason:

* `created_at` records when the audit row was inserted.
* `recorded_at` records when the audited action happened.
* `updated_at` would imply ordinary mutable row lifecycle.
* `deleted_at` would imply ordinary clinical-resource logical deletion semantics.
* audit retention, redaction, purge, and tamper-evidence require separate decisions.

Audit events reference audited resources using:

```text
entity_resource_type
entity_id
```

not foreign keys.

Reason:

* `AuditEvent.entity` may refer to different resource types.
* a single FK cannot point to multiple target tables.
* multiple nullable FKs would be heavier and more fragile.
* audit records should survive ordinary logical deletion and possible future purge workflows.

Current supported entity resource types:

```text
Patient
Observation
Condition
Encounter
```

Current supported actions:

```text
read
search
export
```

Future write-side actions such as:

```text
create
update
delete
```

are deferred to:

```text
BACKLOG / I2+ / EXPAND / Extend AuditAction for clinical write operations
```

Entity-based audit lookup index is deferred to:

```text
BACKLOG / I2 / PERFORMANCE / Add entity-based audit event lookup index
```

---

## 13. Technical timestamps vs clinical dates

Technical timestamps describe persistence operations in this application's database.

Examples:

```text
created_at
updated_at
deleted_at
```

Clinical dates describe the domain meaning of a clinical resource.

Examples:

```text
Observation.effective
Condition.recorded_date
Encounter.period
AuditEvent.recorded
```

Example distinction:

```text
observations.effective_at = 2026-05-20 08:30
observations.created_at = 2026-05-26 12:00
observations.deleted_at = NULL
```

Meaning:

```text
The observation was clinically effective on May 20.
The observation row was inserted into this database on May 26.
The observation is not logically deleted.
```

Audit example:

```text
audit_events.recorded_at = 2026-06-04 10:00
audit_events.created_at = 2026-06-04 10:00:02
```

Meaning:

```text
The audited action happened at 10:00.
The audit row was inserted into this database at 10:00:02.
```

Those are different facts.

Technical timestamps must not be confused with clinical dates.

---

## 14. Code catalog design

Observation and Condition codes use separate catalog tables:

```text
observation_codes
condition_codes
```

The clinical rows reference catalog rows through:

```text
observations.code_id -> observation_codes.id
conditions.code_id   -> condition_codes.id
```

The clinical rows do not duplicate:

```text
code_system
code_code
code_display
```

Reason:

* code catalogs support future UI dropdowns.
* code catalogs avoid repeated code data in clinical rows.
* code catalogs make supported/selectable codes easier to seed and maintain.
* separate catalogs are clearer than a generic code table at this project stage.

A single generic `clinical_codes` table is intentionally deferred.

Future catalog lifecycle may use fields such as:

```text
is_selectable
retired_at
valid_from
valid_to
```

That is outside the current persistence slice.

---

## 15. Reference persistence design

The domain `Reference.resource_type` is constrained to supported resource types.

Current supported values:

```text
Patient
Observation
Condition
Encounter
```

`Observation`, `Condition`, and `Encounter` subjects currently must reference `Patient`.

Therefore, their persistence tables use:

```text
patient_id
```

not:

```text
subject_resource_type
subject_id
```

This keeps the schema relational and aligned with current domain rules.

`AuditEvent.entity` is different because it may reference multiple supported resource types.

Therefore, `audit_events` uses:

```text
entity_resource_type
entity_id
```

not:

```text
patient_id
observation_id
condition_id
encounter_id
```

and not a foreign key.

---

## 16. Index strategy

The current schema avoids simple `patient_id` indexes when a composite index already starts with `patient_id`.

Current clinical composite indexes:

```text
ix_observations_patient_code
ix_observations_patient_effective_at
ix_conditions_patient_code
ix_encounters_patient_period_start_at
```

Reason:

* these indexes support the expected query patterns.
* their first column is `patient_id`.
* they can support many patient-scoped lookups.
* avoiding redundant simple indexes reduces write overhead and storage.
* index additions should remain tied to concrete query patterns.

Current audit index:

```text
ix_audit_events_recorded_at
```

Reason:

* supports listing recent audit events.
* aligns with current `ListAuditEventsUseCase`.
* current use-case orders by recent audit time.

No indexes involving `deleted_at` are introduced yet.

No audit entity lookup index is introduced yet.

Deferred audit entity lookup index:

```text
ix_audit_events_entity(entity_resource_type, entity_id)
```

Tracked by:

```text
BACKLOG / I2 / PERFORMANCE / Add entity-based audit event lookup index
```

Future index changes should be guided by actual adapter queries and, eventually, database query plans.

---

## 17. Alembic migrations

Alembic has been initialized under:

```text
apps/api/alembic/
```

Current Alembic files:

```text
apps/api/
├── alembic.ini
└── alembic/
    ├── env.py
    ├── script.py.mako
    └── versions/
```

Alembic is configured to use:

* `Settings.database_url`
* `Base.metadata`

The `alembic.ini` file prepends `src` to the Python path so Alembic can import the `fhir_gateway` package.

Alembic imports the SQLAlchemy models package so ORM models are registered in `Base.metadata`.

Current migration chain:

```text
<base>
    ↓
f97f9d019499_create_patient_tables
    ↓
ab48a83daad7_add_clinical_resource_tables
    ↓
d4e8f2a1c9b7_add_logical_deletion_columns_to_clinical_resources
    ↓
a6f3c9d2e1b8_add_audit_event_table
```

The migrations were created manually to make the schema explicit and reviewable.

Alembic autogeneration is intentionally deferred until the project has:

* a local PostgreSQL workflow
* a clearer migration review routine
* integration tests around migrations/adapters

Safe Alembic inspection commands:

```text
pipenv run alembic history --verbose
pipenv run alembic heads --verbose
pipenv run alembic upgrade base:head --sql
pipenv run alembic downgrade a6f3c9d2e1b8:d4e8f2a1c9b7 --sql
```

Do not run migrations against PostgreSQL until the local PostgreSQL workflow has been explicitly configured.

---

## 18. Testing

Run persistence tests from:

```text
apps/api
```

Run all persistence tests:

```text
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy
```

Run ORM model tests:

```text
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models
```

Run ORM/domain mapper tests:

```text
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/mappers
```

Run SQLAlchemy read adapter tests:

```text
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/adapters
```

Run architecture boundary tests:

```text
pipenv run pytest tests/unit/architecture
```

Run the full backend test suite:

```text
pipenv run pytest
```

Current validated state:

```text
full test suite passing
```

SQLite test considerations:

Adapter unit tests currently use SQLite in-memory databases for speed and local simplicity.

SQLite is not a full PostgreSQL replacement.

Known SQLite differences affecting adapter tests:

* SQLite does not preserve timezone-aware datetimes like PostgreSQL `TIMESTAMP WITH TIME ZONE`.
* SQLite does not natively support PostgreSQL-specific functions such as `btrim`.

Where needed, adapter tests isolate these differences inside test fixtures or test helpers.

Production-oriented database behavior should later be validated with PostgreSQL integration tests.

---

## 19. Current limitations

The persistence layer does not yet include:

* exposed persistence-backed clinical HTTP endpoints
* local PostgreSQL workflow
* Alembic autogeneration workflow
* integration tests against PostgreSQL
* seed data
* logical delete/restore use-cases
* physical purge workflow
* partial indexes for logically non-deleted rows
* audit event writer adapter
* current-agent provider
* audit event recorder service
* audit middleware
* authentication/authorization integration
* entity-based audit filtering
* advanced audit pagination
* trigger-based `updated_at` hardening
* write-side SQLAlchemy adapters
* domain-to-ORM write mappers

Implemented and no longer listed as limitations:

* SQLAlchemy read adapters
* audit event reader adapter
* HTTP database session dependency
* HTTP adapter dependency wiring
* HTTP use-case dependency wiring

---

## 20. Planned persistence work

Likely next persistence-related work:

1. Protect selected clinical/audit endpoints through Phase 4 security dependencies.
2. Expose selected persistence-backed clinical endpoints in Phase 5.
3. Add local PostgreSQL workflow.
4. Add Alembic autogeneration workflow.
5. Add PostgreSQL integration testing strategy.
6. Add seed data strategy.
7. Add controlled audit event write pipeline.
8. Add audit event writer adapter.
9. Add domain-to-ORM mapping when future write-side use-cases require it.
10. Add filtered and paginated audit event queries when audit UI/API needs them.
11. Add entity-based audit event lookup index when entity-scoped audit queries exist.
12. Add trigger hardening if needed.

---

## 21. Persistence design principles

1. Keep SQLAlchemy isolated to infrastructure.
2. Keep domain entities independent from ORM models.
3. Keep application ports independent from SQLAlchemy.
4. Use ORM/domain mappers at the infrastructure boundary.
5. Use SQLAlchemy adapters to implement application persistence ports.
6. Use HTTP dependencies to compose sessions, adapters and use-cases.
7. Use Alembic for schema changes.
8. Prefer explicit manually reviewed migrations at this stage.
9. Avoid schema expansion without current use-case pressure.
10. Avoid premature generic repositories.
11. Keep routers out of persistence details.
12. Treat technical timestamps as persistence metadata.
13. Treat clinical dates as domain data.
14. Treat audit events as separate from row timestamps.
15. Use logical deletion for top-level clinical resources.
16. Hide logically deleted resources from ordinary reads by default.
17. Do not add indexes until query patterns justify them.
18. Treat audit events as append-oriented records.
19. Do not use ordinary clinical logical deletion for audit events.
20. Do not let arbitrary user-controlled input define audit `agent`.
21. Do not let mappers trigger accidental database queries.
22. Do not commit transactions inside read adapters.
23. Do not create database sessions inside read adapters.
24. Do not expose ORM records outside infrastructure.

---

## 22. Related ADRs

* ADR 0012: SQLAlchemy persistence foundation and mapping boundaries
* ADR 0013: Centralized runtime configuration
* ADR 0014: Database timestamp and audit metadata strategy
* ADR 0015: AuditEvent persistence strategy
* ADR 0016: Clinical resource logical deletion strategy
* ADR 0017: MVP authentication, RBAC, and audit security model

---

## 23. Related backlog items

* BACKLOG / I1-P3 / HARDEN / Prevent accidental lazy loading in SQLAlchemy mappers
* BACKLOG / I1-DEMO / HARDEN / Define curated terminology policy for demo Observation and Condition codes
* BACKLOG / I1-DEMO / HARDEN / Define curated Quantity.unit policy for demo clinical observations
* BACKLOG / I1-MVP-CLOSURE / HARDEN / Add Patient name representation database constraint
* BACKLOG / I2 / EXPAND / Add filtered and paginated audit event queries
* BACKLOG / I2 / PERFORMANCE / Add entity-based audit event lookup index
* BACKLOG / I2+ / EXPAND / Extend AuditAction for clinical write operations
* BACKLOG / I2+ / EXPAND / Add domain-to-ORM mapping for write use-cases
* BACKLOG / POST-MVP / HARDEN / Add database triggers for `updated_at` consistency
