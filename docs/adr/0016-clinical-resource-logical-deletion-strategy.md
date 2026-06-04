# ADR 0016: Clinical resource logical deletion strategy

## Status

Accepted

## Date

2026-06-04

## Context

Phase 3 has introduced the SQLAlchemy/Alembic persistence foundation and the first clinical persistence schemas:

- Patient
- Patient identifiers
- Observation codes
- Condition codes
- Observation
- Condition
- Encounter

The project is still before the implementation of:

- ORM/domain mappers
- SQLAlchemy adapters
- persistence-backed HTTP endpoints
- request-scoped SQLAlchemy sessions
- seed data
- local PostgreSQL workflow
- clinical write use-cases

This is the right moment to define deletion semantics for persisted clinical resources.

Clinical resources may need to become unavailable to ordinary application reads without physically removing their database rows.

Physical deletion is dangerous in a healthcare-style system because it can conflict with:

- traceability
- auditability
- historical reconstruction
- future export behavior
- future security/compliance requirements
- references from audit events
- references from dependent clinical resources

The project already has foreign keys such as:

    patient_identifiers.patient_id -> patients.id
    observations.patient_id -> patients.id
    conditions.patient_id -> patients.id
    encounters.patient_id -> patients.id

Some of these foreign keys currently use:

    ON DELETE CASCADE

That is acceptable for exceptional physical purge workflows, but physical deletion should not be the normal application-level deletion behavior for clinical resources.

The project needs an explicit strategy before mappers and adapters start encoding query behavior.

---

## Decision

Use logical deletion for top-level clinical resources.

Application-level deletion of clinical resources should not physically delete rows by default.

Instead, top-level clinical resource tables should receive a nullable timestamp column:

    deleted_at

The meaning is:

    deleted_at IS NULL
        The resource is not logically deleted and is visible to ordinary application reads.

    deleted_at IS NOT NULL
        The resource is logically deleted and should be hidden from ordinary application reads.

The following tables receive `deleted_at`:

- `patients`
- `observations`
- `conditions`
- `encounters`

The following tables do not receive `deleted_at` in this decision:

- `patient_identifiers`
- `observation_codes`
- `condition_codes`
- `audit_events`

The `deleted_at` column is:

- timezone-aware
- nullable
- technical/application lifecycle metadata
- not part of the current domain entities by default
- not exposed through public HTTP responses by default

The normal future application behavior should be:

    delete clinical resource
        -> set deleted_at = now()

not:

    delete clinical resource
        -> DELETE FROM table

Physical deletion is reserved for exceptional purge, maintenance, test cleanup, or future explicitly approved retention workflows.

---

## Why `deleted_at` instead of `active`

Do not use a generic boolean column such as:

    active
    is_active

for logical deletion.

Reasons:

1. `active` is ambiguous.
2. `active = false` can mean inactive, archived, deleted, cancelled, superseded, clinically not current, or not selectable.
3. In FHIR-like contexts, `Patient.active` has domain meaning and should not be confused with persistence-level logical deletion.
4. A boolean does not record when the deletion happened.
5. A boolean can become inconsistent if paired later with a timestamp.

Preferred representation:

    deleted_at TIMESTAMP WITH TIME ZONE NULL

This provides both deletion state and deletion time in one column.

---

## Why not `is_deleted` plus `deleted_at`

Do not introduce both:

    is_deleted
    deleted_at

at this stage.

The two columns can become inconsistent.

Examples:

    is_deleted = true
    deleted_at = NULL

    is_deleted = false
    deleted_at = 2026-06-04T18:30:00Z

Using only `deleted_at` avoids this ambiguity.

The deletion state is derived from the timestamp:

    deleted_at IS NULL
    deleted_at IS NOT NULL

---

## Affected tables

### `patients`

Add:

    deleted_at TIMESTAMP WITH TIME ZONE NULL

Reason:

Patient is a top-level clinical resource.

A logically deleted patient should normally be hidden from ordinary patient search and patient retrieval use-cases.

---

### `observations`

Add:

    deleted_at TIMESTAMP WITH TIME ZONE NULL

Reason:

Observation is a top-level clinical resource.

A logically deleted observation should normally be hidden from ordinary observation listing and patient summary use-cases.

---

### `conditions`

Add:

    deleted_at TIMESTAMP WITH TIME ZONE NULL

Reason:

Condition is a top-level clinical resource.

A logically deleted condition should normally be hidden from ordinary patient summary and patient bundle use-cases.

---

### `encounters`

Add:

    deleted_at TIMESTAMP WITH TIME ZONE NULL

Reason:

Encounter is a top-level clinical resource.

A logically deleted encounter should normally be hidden from ordinary patient summary and patient bundle use-cases.

---

## Tables intentionally not affected

### `patient_identifiers`

Do not add `deleted_at` to `patient_identifiers`.

Reason:

Patient identifiers are dependent component records of `patients`.

If a patient is logically deleted, ordinary application reads should not expose that patient or its identifiers.

Identifier-level lifecycle can be introduced later if a concrete requirement appears.

---

### `observation_codes`

Do not add `deleted_at` to `observation_codes`.

Reason:

Observation codes are catalog/terminology records, not clinical resources.

Terminology/catalog lifecycle should use a different model if needed later, such as:

    is_selectable
    retired_at
    valid_from
    valid_to

That is outside this ADR.

---

### `condition_codes`

Do not add `deleted_at` to `condition_codes`.

Reason:

Condition codes are catalog/terminology records, not clinical resources.

Terminology/catalog lifecycle should be handled separately.

---

### `audit_events`

Do not add `deleted_at` to `audit_events`.

Reason:

Audit events are append-oriented historical records.

They should not follow ordinary clinical resource deletion semantics.

Audit retention, redaction, hiding, tamper evidence, and purge policies require a separate audit/security decision.

---

## ORM strategy

Introduce a reusable SQLAlchemy mixin for logical deletion metadata.

Class:

    LogicalDeletionMixin

Location:

    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/mixins.py

Column:

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

Apply `LogicalDeletionMixin` to:

- `PatientRecord`
- `ObservationRecord`
- `ConditionRecord`
- `EncounterRecord`

Do not apply `LogicalDeletionMixin` to:

- `PatientIdentifierRecord`
- `ObservationCodeRecord`
- `ConditionCodeRecord`
- future `AuditEventRecord`

`LogicalDeletionMixin` is independent from `TimestampMixin`.

A resource can use both:

    LogicalDeletionMixin
    TimestampMixin

but audit events should not use the same pattern by default because audit events have separate append-oriented semantics.

---

## Domain model strategy

Do not add `deleted_at` to the current domain entities in this correction.

Affected domain entities remain:

- `Patient`
- `Observation`
- `Condition`
- `Encounter`

Reason:

At the current stage, logical deletion is a persistence/application visibility concern.

The ordinary domain entities represent resources available to application use-cases.

Future delete/restore/admin use-cases may introduce explicit application models or domain concepts if needed.

For now, mappers/adapters should hide logically deleted resources from ordinary reads.

---

## Adapter/query strategy

Future SQLAlchemy adapters must filter logically deleted resources out of ordinary reads by default.

Default condition:

    deleted_at IS NULL

Examples:

Patient lookup:

    SELECT *
    FROM patients
    WHERE id = :patient_id
      AND deleted_at IS NULL

Patient observations:

    SELECT *
    FROM observations
    WHERE patient_id = :patient_id
      AND deleted_at IS NULL

Patient conditions:

    SELECT *
    FROM conditions
    WHERE patient_id = :patient_id
      AND deleted_at IS NULL

Patient encounters:

    SELECT *
    FROM encounters
    WHERE patient_id = :patient_id
      AND deleted_at IS NULL

Admin/audit/maintenance queries may later opt into including logically deleted rows, but that requires explicit design.

---

## API strategy

Public HTTP APIs should not expose `deleted_at` by default.

Ordinary clinical endpoints should behave as if logically deleted resources do not exist.

Potential future behavior:

    GET /patients/{id}

If the patient exists but `deleted_at IS NOT NULL`, the ordinary endpoint may return:

    404 Not Found

or another deliberately designed response.

The exact HTTP error behavior should be decided when persistence-backed endpoints are implemented.

This ADR only establishes the persistence deletion strategy.

---

## Migration strategy

Do not edit historical migrations that have already been reviewed and committed.

Create a new manual Alembic migration after the clinical resource migration.

The new migration adds nullable `deleted_at` columns to:

- `patients`
- `observations`
- `conditions`
- `encounters`

The migration does not add:

- indexes
- triggers
- seed data
- adapters
- mappers
- HTTP behavior
- domain fields
- physical delete workflows

Downgrade removes the columns.

---

## Index strategy

Do not add new indexes for `deleted_at` in this correction.

Reason:

- there are no SQLAlchemy adapters yet
- there are no query plans yet
- there is no local PostgreSQL workflow yet
- the project has been intentionally conservative with indexes
- adding partial indexes now would be premature

Future PostgreSQL-specific optimization may introduce partial indexes such as:

    WHERE deleted_at IS NULL

but only after real adapter queries and performance needs exist.

Existing indexes remain unchanged.

---

## Relationship with foreign keys and cascade behavior

Existing foreign keys with `ON DELETE CASCADE` may remain.

This ADR changes normal application deletion behavior, not exceptional physical purge behavior.

Normal application deletion:

    UPDATE patients
    SET deleted_at = now()
    WHERE id = :patient_id

Exceptional physical purge:

    DELETE FROM patients
    WHERE id = :patient_id

Physical purge may still cascade according to database constraints.

That is acceptable only for explicit purge/maintenance workflows, not ordinary application-level deletion.

---

## Relationship with AuditEvent

This ADR supports the future audit persistence strategy.

Audit events should be able to reference resources historically even if those resources are logically deleted.

Logical deletion reduces the likelihood of broken audit references because clinical rows normally remain physically present.

However, this ADR does not require audit events to use foreign keys to clinical resource tables.

The future audit persistence strategy may still use logical polymorphic references such as:

    entity_resource_type
    entity_id

because `AuditEvent.entity` can reference different resource types.

Audit events should not be physically deleted or logically deleted as part of ordinary clinical resource deletion.

---

## Considered options

### Option A: Physical deletion by default

Application delete operations would use:

    DELETE FROM table

Advantages:

- simple database model
- no extra columns
- no filtering needed in queries

Disadvantages:

- loses historical clinical rows
- weakens auditability
- can cascade delete dependent data
- complicates future audit trail semantics
- makes future recovery impossible without backups
- poor fit for healthcare-style traceability

Decision:

Rejected.

---

### Option B: Boolean `active`

Application delete operations would set:

    active = false

Advantages:

- simple to understand initially
- easy to filter

Disadvantages:

- ambiguous semantics
- conflicts with FHIR-like `Patient.active` meaning
- does not record deletion time
- can be confused with clinical status
- may require later migration to timestamp anyway

Decision:

Rejected.

---

### Option C: Boolean `is_deleted` plus `deleted_at`

Application delete operations would set:

    is_deleted = true
    deleted_at = now()

Advantages:

- explicit boolean state
- deletion time available

Disadvantages:

- redundant state
- possible inconsistencies
- more columns than needed
- no current need for both

Decision:

Rejected for now.

Can be reconsidered later if query clarity or database-specific constraints justify it.

---

### Option D: Nullable `deleted_at`

Application delete operations set:

    deleted_at = now()

Advantages:

- clear semantics
- records deletion time
- avoids conflict with FHIR-like active status
- avoids redundant state
- supports ordinary filtering with `deleted_at IS NULL`
- keeps rows available for audit/history
- easy to add before mappers/adapters exist

Disadvantages:

- every ordinary read must remember to filter `deleted_at IS NULL`
- unique constraints may need future review if ID reuse is ever allowed
- indexes may need future optimization
- domain/application delete behavior still needs future use-case design

Decision:

Accepted.

---

## Consequences

### Positive consequences

- Clinical rows remain physically present after ordinary deletion.
- Future audit references are more stable.
- Future adapters can consistently hide deleted resources.
- The deletion time is recorded.
- The design avoids overloading `active`.
- The correction happens before mappers/adapters/endpoints, reducing future refactor cost.
- Existing physical cascade behavior can remain reserved for explicit purge workflows.

---

### Negative consequences

- ORM models and migrations need an additional correction now.
- Documentation must be updated.
- Tests must be updated.
- Future adapters must consistently filter out logically deleted rows.
- Query performance may later require partial indexes.
- The project must clearly distinguish logical deletion from physical purge.

---

### Mitigations

- Add `LogicalDeletionMixin` to centralize the column definition.
- Add ORM tests verifying `deleted_at` exists only on intended tables.
- Add migration SQL validation.
- Document the default query rule.
- Do not add premature indexes.
- Add future adapter tests ensuring logically deleted rows are excluded from ordinary reads.
- Keep physical purge explicitly out of ordinary application behavior.

---

## Implementation timing

This correction is implemented before:

- AuditEvent ORM model and migration
- ORM/domain mappers
- SQLAlchemy adapters
- persistence-backed HTTP endpoints
- seed data

Reason:

Adapters and endpoints should be born with the correct deletion semantics.

Adding logical deletion after adapters exist would require broader refactoring.

---

## Future work

Future work may include:

- application-level delete use-cases
- restore/undelete use-cases
- admin queries including deleted resources
- retention policies
- physical purge workflows
- PostgreSQL partial indexes for non-deleted rows
- integration tests against PostgreSQL
- audit events for clinical delete/restore operations
- HTTP error semantics for logically deleted resources

These are outside this ADR.

---

## Related ADRs

- ADR 0012: SQLAlchemy persistence foundation and mapping boundaries
- ADR 0014: Database timestamp and audit metadata strategy
- Future ADR 0015: AuditEvent persistence strategy

---

## Decision outcome

Use `deleted_at` as the logical deletion marker for top-level clinical resources.

Apply it to:

- `patients`
- `observations`
- `conditions`
- `encounters`

Do not apply it to:

- `patient_identifiers`
- `observation_codes`
- `condition_codes`
- `audit_events`

Do not use `active` or `is_deleted` for this correction.

Do not physically delete clinical resources by default in ordinary application behavior.

Do not add new indexes yet.

Do not expose `deleted_at` through public HTTP APIs by default.

Implement this correction before mappers, adapters, AuditEvent persistence, and persistence-backed endpoints.
