# ADR 0014: Database timestamp and audit metadata strategy

## Status

Accepted

## Date

2026-05-28

## Phase

Phase 3 — Backend foundation

---

## Context

Phase 3 introduces SQLAlchemy persistence incrementally.

The project already has an initial Patient persistence schema.

The `patients` table includes technical timestamp columns:

    created_at
    updated_at

The dependent `patient_identifiers` table does not include those columns.

The project is about to introduce additional persistence tables for:

    observation_codes
    condition_codes
    observations
    conditions
    encounters

Before adding more ORM models, the project needs a consistent database-wide strategy for technical row timestamps.

The project also has a domain `AuditEvent` entity and an application use-case for listing audit events.

Therefore, the project needs to distinguish clearly between:

- technical row timestamps
- clinical dates
- audit events

---

## Problem

Without a documented strategy, future persistence tables may handle timestamps inconsistently.

Possible inconsistencies include:

    some tables have created_at and updated_at
    some tables only have created_at
    some tables have no timestamps
    audit_events uses updated_at incorrectly
    clinical dates are confused with row timestamps
    row timestamps are exposed through HTTP APIs without a clear reason
    domain entities start receiving persistence metadata accidentally

This would make the persistence model harder to explain, harder to test, and harder to evolve.

---

## Decision

Use technical `created_at` and `updated_at` timestamps on top-level ORM-managed tables.

Do not add technical timestamps to dependent component tables by default.

Do not map `created_at` and `updated_at` into domain entities by default.

Do not expose technical row timestamps through HTTP APIs by default.

Treat `AuditEvent` as a separate audit trail concept, not as a substitute for row timestamps.

Treat row timestamps as technical persistence metadata, not as a substitute for `AuditEvent`.

Use database server defaults and SQLAlchemy `onupdate` in Phase 3.

Do not introduce database triggers yet.

Introduce a reusable SQLAlchemy `TimestampMixin` for timestamped ORM models.

---

## Definitions

### Technical row timestamps

Technical row timestamps describe persistence operations in this application's database.

Examples:

    created_at
    updated_at

Meaning:

    when a row was inserted into this database
    when a row was last updated in this database

They are infrastructure metadata.

They are not domain facts by default.

---

### Clinical dates

Clinical dates describe the actual clinical meaning of a resource.

Examples:

    Observation.effective
    Condition.recorded_date
    Encounter.period

These dates belong to the domain model.

Example:

    observations.effective_at = 2026-05-20 08:30
    observations.created_at = 2026-05-26 12:00

Meaning:

    The observation was clinically effective on May 20.
    The row was inserted into this database on May 26.

Those are different facts.

---

### Audit events

Audit events describe actions performed in the system.

Examples:

    read
    search
    export

An audit event may record:

    who performed the action
    what action was performed
    which entity was affected
    when the action happened

This is different from:

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

## Selected convention

### Top-level ORM-managed tables

Top-level ORM-managed tables should include:

    created_at
    updated_at

Both columns must be:

    timezone-aware
    non-nullable
    technical persistence metadata

Current and planned examples:

    patients
    observation_codes
    condition_codes
    observations
    conditions
    encounters

Reason:

These tables represent independently meaningful persistence records.

They may be inserted, corrected, seeded, updated, imported, or administratively maintained.

Technical timestamps are useful for debugging, maintenance, import workflows, and operational visibility.

---

### Dependent component tables

Dependent component tables do not receive `created_at` and `updated_at` by default.

Current example:

    patient_identifiers

Reason:

`patient_identifiers` is currently a dependent table owned by `patients`.

It is not modeled as an independently managed resource.

If a patient identifier is added, removed, or changed, the relevant top-level record is the patient.

The project may revisit this decision later if identifiers become independently managed records with their own lifecycle.

---

### Catalog tables

Catalog tables are considered top-level ORM-managed tables.

Therefore, planned catalog tables should include:

    created_at
    updated_at

Examples:

    observation_codes
    condition_codes

Reason:

Catalog rows may be seeded, corrected, expanded, or administratively maintained.

Example:

    display = "Glucose"

may later be corrected to:

    display = "Glucose [Mass/volume] in Blood"

It is useful to know when the catalog row was created or last modified.

---

### Clinical resource tables

Clinical resource tables are considered top-level ORM-managed tables.

Therefore, planned clinical resource tables should include:

    created_at
    updated_at

Examples:

    observations
    conditions
    encounters

These timestamps describe persistence operations.

They do not describe when the clinical event occurred.

---

## SQLAlchemy implementation strategy

Introduce a reusable SQLAlchemy mixin.

Suggested file:

    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/mixins.py

Suggested class:

    TimestampMixin

Purpose:

- avoid repeating timestamp column definitions across ORM models
- keep timestamp behavior consistent
- make future timestamp changes easier
- clearly mark timestamp behavior as an infrastructure concern

Expected technical pattern:

    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

The exact implementation may be adjusted to match SQLAlchemy typing requirements.

Expected usage:

    class ObservationRecord(TimestampMixin, Base):
        ...

    class ConditionRecord(TimestampMixin, Base):
        ...

    class EncounterRecord(TimestampMixin, Base):
        ...

The existing `PatientRecord` may later be refactored to inherit from `TimestampMixin`.

That refactor should not change the database schema if the column definitions remain equivalent.

---

## Alembic migration strategy

Alembic migrations should create timestamp columns explicitly.

Expected migration pattern:

    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )

    sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )

Migrations should not create trigger functions or triggers in Phase 3.

If trigger-based hardening is later adopted, it should be introduced through a dedicated migration.

---

## Why not database triggers now

Database triggers are not introduced in Phase 3.

The selected Phase 3 approach is:

    server_default=func.now()
    onupdate=func.now()

instead of trigger-based timestamp enforcement.

Reasons:

- triggers are more database-specific
- triggers add operational complexity
- triggers require stronger PostgreSQL integration testing
- triggers make the first persistence slices harder to understand
- the current project stage is still establishing basic persistence
- current writes are expected to go through SQLAlchemy adapters
- there are no external writers yet
- there is no direct SQL ingestion workflow yet
- the project does not yet rely on `updated_at` for synchronization or production operations

Known limitation:

    Direct SQL updates outside SQLAlchemy may not update updated_at.

This limitation is accepted for the current phase.

Trigger-based `updated_at` enforcement is tracked separately as future hardening:

    BACKLOG / HARDEN / P3+ / Add database triggers for updated_at consistency

---

## AuditEvent persistence

AuditEvent persistence must be designed separately.

A future `audit_events` table should be append-only or append-oriented.

Expected principle:

    AuditEvent.recorded represents when the auditable action happened.
    created_at, if used, represents when the audit row was inserted.
    updated_at should be avoided unless there is a strong reason.

The exact `AuditEventRecord` schema belongs to the future AuditEvent persistence sub-issue.

---

## Domain impact

Domain entities should not gain `created_at` or `updated_at` by default.

Technical row timestamps remain an infrastructure concern.

Domain entities should only contain dates that have domain meaning.

Examples:

    Observation.effective
    Condition.recorded_date
    Encounter.period
    AuditEvent.recorded

Those are domain concepts.

They are not generic persistence timestamps.

---

## API impact

Technical row timestamps should not be exposed through HTTP APIs by default.

Future HTTP schemas may expose them only if there is a clear product, debugging, synchronization, or admin requirement.

Clinical API responses should prioritize domain-relevant dates.

Examples:

    Observation.effective
    Condition.recorded_date
    Encounter.period
    AuditEvent.recorded

---

## Alternatives considered

### Alternative A — Add timestamps to every table

This would add `created_at` and `updated_at` to all tables, including dependent component tables.

Rejected.

Reason:

Not every table has an independent lifecycle.

Adding timestamps mechanically to every table creates unnecessary noise and may confuse dependent records with independently managed records.

---

### Alternative B — Keep timestamps only on Patient

This would leave timestamps only on the `patients` table.

Rejected.

Reason:

The persistence layer is expanding.

Future top-level clinical tables and catalog tables should have consistent technical metadata.

Leaving timestamps only on Patient would look accidental.

---

### Alternative C — Use database triggers immediately

This would make the database responsible for updating `updated_at` on every update.

Rejected for Phase 3.

Reason:

Although triggers are more robust, they are premature for the current project stage.

The project does not yet have:

- local PostgreSQL workflow fully established
- migration integration tests
- external writers
- production-like deployment
- direct SQL ingestion paths
- operational dependency on `updated_at`

Triggers remain a future hardening option.

---

### Alternative D — Map timestamps into domain entities

This would add `created_at` and `updated_at` to domain entities such as `Patient`, `Observation`, `Condition`, or `Encounter`.

Rejected.

Reason:

Technical persistence timestamps are not domain concepts by default.

Domain entities should contain dates with domain meaning.

Examples:

    Observation.effective
    Condition.recorded_date
    Encounter.period
    AuditEvent.recorded

Generic persistence timestamps should remain in infrastructure unless a future requirement explicitly promotes them.

---

## Consequences

### Positive consequences

- Timestamp behavior becomes consistent before more ORM models are added.
- Sub-issue E can use a clear convention.
- `TimestampMixin` reduces duplication.
- Domain entities remain persistence-agnostic.
- Audit trail semantics remain separate from technical row metadata.
- Trigger complexity is deferred until the project needs it.
- Future reviewers can understand why some tables have timestamps and others do not.

---

### Negative consequences

- `updated_at` is not fully database-enforced in Phase 3.
- Direct SQL updates may bypass SQLAlchemy `onupdate`.
- A future migration may be needed if trigger-based hardening is adopted.
- The project must clearly document that technical timestamps are not audit events.
- The project must consistently classify tables as top-level or dependent.

---

## Impact on existing Patient schema

No change is required to the existing Patient persistence schema.

Current state remains valid:

    patients:
        created_at
        updated_at

    patient_identifiers:
        no created_at
        no updated_at

This matches the selected convention:

    patients is a top-level ORM-managed table.
    patient_identifiers is a dependent component table.

---

## Impact on Sub-issue E

Sub-issue E should add `created_at` and `updated_at` to:

    observation_codes
    condition_codes
    observations
    conditions
    encounters

Sub-issue E should introduce or use:

    TimestampMixin

Sub-issue E should not introduce database triggers.

Sub-issue E should keep clinical dates separate:

    observations.effective_at
    conditions.recorded_at
    encounters.period_start_at
    encounters.period_end_at

---

## Impact on future AuditEvent persistence

The future `AuditEventRecord` schema must not blindly copy the same mutable timestamp pattern.

Audit events should be treated as append-only or append-oriented records.

The future AuditEvent persistence sub-issue must decide whether audit rows need:

    created_at

but should avoid:

    updated_at

unless a strong reason exists.

`AuditEvent.recorded` remains the domain timestamp for when the auditable action occurred.

---

## Related backlog items

This ADR resolves:

    BACKLOG / HARDEN / P3 / Define database-wide timestamp and audit column strategy

This ADR creates or confirms future hardening work:

    BACKLOG / HARDEN / P3+ / Add database triggers for updated_at consistency

---

## Related ADRs

- ADR 0012: SQLAlchemy persistence foundation and mapping boundaries
- ADR 0013: Centralized runtime configuration

---

## Final decision summary

Use:

    created_at
    updated_at

on top-level ORM-managed tables.

Do not add them to dependent component tables by default.

Keep technical timestamps out of domain entities by default.

Keep technical timestamps out of public HTTP APIs by default.

Keep audit events separate from row timestamps.

Use:

    server_default=func.now()
    onupdate=func.now()

for Phase 3.

Introduce:

    TimestampMixin

Do not use database triggers now.

Track database trigger enforcement as a future hardening backlog item.
