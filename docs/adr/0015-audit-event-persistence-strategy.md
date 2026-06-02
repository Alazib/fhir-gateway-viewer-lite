# ADR 0015: AuditEvent persistence strategy

## Status

Accepted

## Date

2026-06-02

## Context

The project includes a domain-level `AuditEvent` entity and an application-level `ListAuditEvents` use-case.

The current domain entity is:

    AuditEvent

with these required attributes:

    id: ResourceId
    recorded: Instant
    agent: str
    action: AuditAction
    entity: Reference

The current audit action enum is:

    read
    search
    export

The current `agent` field is a required normalized string.

It is deliberately not modeled as an enum, catalog table, or foreign key in the domain.

The current `ListAuditEventsUseCase` only supports listing recent audit events:

    list_recent(limit)

The use-case validates:

    limit

and does not currently filter by:

    agent
    action
    entity
    date range

Phase 3 introduces the persistence foundation for the current core entities required by the Phase 2 application use-cases:

- Patient
- Patient identifiers
- Observation
- Condition
- Encounter
- AuditEvent

Patient, Observation, Condition, and Encounter persistence schemas have already been introduced through SQLAlchemy ORM models and Alembic migrations.

The next persistence schema is `AuditEvent`.

Audit event persistence is conceptually different from ordinary clinical resource persistence.

Clinical resources represent current clinical data.

Audit events represent historical traces of actions performed in or through the system.

This distinction affects:

- table mutability expectations
- timestamp semantics
- entity reference strategy
- deletion behavior
- future audit enforcement
- future security and compliance work
- how the `agent` field should be produced
- how the audit action taxonomy should evolve

The project must introduce an `AuditEventRecord` schema for listing recent audit events, but must not implement the full audit write pipeline in this phase.

Full audit write enforcement belongs to a later phase.

---

## Decision

Persist audit events as append-oriented records in an `audit_events` table.

The table will support the current domain/application need of listing recent audit events.

The initial persistence model will use:

- string resource id as primary key
- required audit timestamp
- required free-form agent string
- required closed audit action string
- audited entity represented as resource type plus resource id
- technical row insertion timestamp

The table will not use the shared `TimestampMixin` by default.

The table will not include `updated_at` by default.

The audited entity will be represented by:

    entity_resource_type
    entity_id

The audited entity will not be represented by polymorphic foreign keys.

The audited entity will not be represented by multiple nullable columns such as:

    patient_id
    observation_id
    condition_id
    encounter_id

The initial table will include an index supporting recent audit event listing by:

    recorded_at

The entity-based lookup index:

    ix_audit_events_entity

will be deferred to a backlog item:

    BACKLOG / EXPAND / P3+ / Add entity-based audit event lookup index

The current audit action set will remain:

    read
    search
    export

This is sufficient for the current read-side and export-side use-cases.

It is not intended to be the final audit action taxonomy.

Future clinical write operations should extend `AuditAction` through:

    BACKLOG / EXPAND / P3+ / Extend AuditAction for clinical write operations

The audit persistence schema must remain infrastructure-only.

Domain and application layers must not import SQLAlchemy or ORM models.

---

## Required table

The initial table should be named:

    audit_events

Expected columns:

| Column | Type | Nullable | Purpose |
|---|---:|---:|---|
| `id` | string | no | Stores `ResourceId.value`; primary key |
| `recorded_at` | timezone-aware datetime | no | Maps `AuditEvent.recorded`; when the audited action happened |
| `agent` | string | no | Required free-form actor/system/client string |
| `action` | string | no | Maps `AuditAction.value` |
| `entity_resource_type` | string | no | Maps `AuditEvent.entity.resource_type` |
| `entity_id` | string | no | Maps the referenced resource id |
| `created_at` | timezone-aware datetime | no | Technical row insertion timestamp |

The initial table should not include:

    updated_at

---

## Required constraints

Expected constraints:

| Name | Type | Purpose |
|---|---|---|
| primary key on `id` | primary key | Identifies each persisted audit event |
| `ck_audit_events_action_allowed` | check constraint | Restrict action to current `AuditAction` values |
| `ck_audit_events_entity_resource_type_allowed` | check constraint | Restrict entity resource type to currently supported resource types |
| `ck_audit_events_agent_not_empty` | check constraint | Prevent blank agent values |

Allowed `action` values:

    read
    search
    export

Allowed `entity_resource_type` values:

    Patient
    Observation
    Condition
    Encounter

The exact supported entity resource types should align with the current domain `Reference.resource_type` rules.

---

## Required indexes

The initial required index is:

| Name | Columns | Purpose |
|---|---|---|
| `ix_audit_events_recorded_at` | `recorded_at` | Supports listing recent audit events |

The entity lookup index is intentionally deferred:

| Name | Columns | Reason for deferral |
|---|---|---|
| `ix_audit_events_entity` | `entity_resource_type`, `entity_id` | No current use-case filters audit events by entity |

The deferred index is tracked by:

    BACKLOG / EXPAND / P3+ / Add entity-based audit event lookup index

---

## Current AuditAction scope

The current allowed actions are:

    read
    search
    export

These actions are sufficient for the current Phase 2 read-side and export-side use-cases.

They are not intended to be the final audit action taxonomy.

Future clinical write capabilities should extend `AuditAction` with actions such as:

    create
    update
    delete

When that happens, the following must be updated:

- domain enum
- domain tests
- application tests that construct audit events
- ORM tests
- Alembic check constraint
- persistence documentation
- this ADR if the taxonomy changes materially

This future work is tracked by:

    BACKLOG / EXPAND / P3+ / Extend AuditAction for clinical write operations

---

## Rationale

### Audit events are not ordinary mutable resources

An audit event is a historical statement that an action happened.

Examples:

- a user read a patient summary
- a user searched patients
- a user exported a patient bundle
- the system listed observations for a patient

Once recorded, an audit event should generally be treated as append-oriented history.

Updating an audit row silently would weaken its meaning as a trace.

For this reason, the initial schema does not include `updated_at`.

If future requirements need correction, redaction, supersession, or invalidation of audit records, those concepts should be modeled explicitly rather than handled as ordinary row updates.

---

### `recorded_at` and `created_at` mean different things

`recorded_at` is the audit/domain timestamp.

It maps to:

    AuditEvent.recorded

It means:

    when the audited action happened

`created_at` is technical persistence metadata.

It means:

    when the audit row was inserted into this application's database

These values may be the same in simple cases, but they are not conceptually identical.

Example:

An event happened at:

    2026-06-02T10:00:00Z

but was persisted at:

    2026-06-02T10:00:02Z

Then:

    recorded_at = 2026-06-02T10:00:00Z
    created_at = 2026-06-02T10:00:02Z

The audit event time and database insertion time must not be collapsed into one concept.

---

### `agent` is required but not enumerated

The domain currently requires:

    agent: str

and normalizes it as a required string.

The domain deliberately does not define:

    AuditAgent

and does not restrict `agent` to a closed set.

This is correct because real agents are dynamic.

An agent may later represent:

    user:alberto
    user:99830132
    system:fhir-gateway
    system:seed-loader
    client:internal-api
    anonymous:demo

Therefore, `agent` should be persisted as:

    agent VARCHAR NOT NULL

not as:

    agent_id
    agent_type
    agent enum
    foreign key to users
    foreign key to agents

However, free-form persistence does not mean user-controlled input.

The value of `agent` must be supplied by trusted runtime context.

Future audit creation should obtain `agent` from infrastructure/application composition, such as:

    authenticated principal
    system identity
    background job identity
    API client identity
    local demo identity

The user should not be allowed to send an arbitrary `agent` value in a clinical request body.

---

### Future agent sourcing strategy

The future audit write pipeline should introduce a controlled source for the current actor.

Possible names:

    CurrentAgentProvider
    CurrentActorProvider
    AuditContext
    AuthenticatedPrincipal
    AuditEventRecorder

The exact name can be decided later.

The intended flow is:

    HTTP request / background job / internal process
        -> trusted runtime context resolves current agent
        -> use-case or audit recorder receives current agent
        -> AuditEvent is created
        -> AuditEventRecord is persisted

For authenticated HTTP requests, `agent` should come from the authenticated principal.

For system processes, `agent` should come from configured system identity.

For local/demo mode, `agent` may come from a controlled development identity.

Examples:

    user:99830132
    system:fhir-gateway
    system:demo
    client:internal-api

This preserves consistency without prematurely creating a user table, agent catalog, or agent enum.

---

### `action` is a closed domain enum

Unlike `agent`, `action` is intentionally closed.

The current domain enum is:

    AuditAction.READ = "read"
    AuditAction.SEARCH = "search"
    AuditAction.EXPORT = "export"

Therefore, the database should enforce allowed values with:

    ck_audit_events_action_allowed

The migration should freeze these values explicitly.

Migrations are historical schema steps and should not import the live domain enum directly.

If the domain enum changes later, a new migration should update the database check constraint.

Future write-side action expansion is tracked by:

    BACKLOG / EXPAND / P3+ / Extend AuditAction for clinical write operations

---

### Audit entity references should be logical references

Clinical resources such as Observation, Condition, and Encounter currently reference Patient through direct relational foreign keys because their domain subject must be a Patient.

Audit events are different.

An audit event may refer to different resource types:

- Patient
- Observation
- Condition
- Encounter

Using a single `patient_id` column would be too narrow.

Using several nullable columns would be awkward and fragile.

Using polymorphic foreign keys would add complexity too early.

Therefore, the audited entity is persisted as a logical reference:

    entity_resource_type
    entity_id

Example:

| id | recorded_at | agent | action | entity_resource_type | entity_id |
|---|---|---|---|---|---|
| `audit-001` | `2026-06-02T10:00:00Z` | `user:99830132` | `read` | `Patient` | `pat-001` |
| `audit-002` | `2026-06-02T10:05:00Z` | `system:fhir-gateway` | `search` | `Observation` | `obs-001` |

This aligns with the domain concept of referencing resources while keeping the audit schema simple and durable.

---

### Audit records should survive deletion of audited resources

Audit logs often need to preserve historical traces even if the resource they refer to is later deleted, archived, or transformed.

A direct foreign key with cascade delete would be dangerous because deleting a clinical row could delete the audit trace.

A direct foreign key with restrict or no-action behavior would preserve the audit row, but would also block deletion of the referenced clinical resource while audit rows still reference it.

That is not the desired default behavior for the initial Phase 3 audit schema.

Therefore, the initial audit schema should not enforce a database foreign key from `audit_events.entity_id` to the referenced clinical resource table.

The application/domain layer and future mappers/adapters are responsible for constructing valid audit references.

A database check constraint may still restrict `entity_resource_type` to the supported resource types.

---

## Considered options

### Option A: Direct nullable foreign keys per resource type

Example columns:

    patient_id
    observation_id
    condition_id
    encounter_id

Advantages:

- relational links are explicit
- database can enforce each FK
- joins are straightforward for each resource type

Disadvantages:

- many nullable columns
- weak invariant: exactly one target column should be populated
- more check constraints
- schema becomes harder to extend
- audit event shape becomes tied to current resource tables
- deletion behavior becomes complicated
- not needed for current `ListAuditEvents` use-case

Decision:

Rejected.

This is too heavy for the current scope.

---

### Option B: Polymorphic logical reference

Example columns:

    entity_resource_type
    entity_id

Advantages:

- simple schema
- supports multiple resource types
- aligns with domain `Reference`
- avoids premature polymorphic FK complexity
- audit records can survive resource deletion
- resource deletion is not blocked by audit rows
- sufficient for recent audit event listing
- can be indexed later for entity-based lookup

Disadvantages:

- database does not enforce that `entity_id` exists in the referenced table
- joins require application logic or conditional queries
- invalid references must be prevented by mappers/adapters and tests

Decision:

Accepted.

This is the best trade-off for Phase 3.

---

### Option C: Generic audited resource table

Example:

    audited_resources
    audit_events.entity_ref_id -> audited_resources.id

Advantages:

- centralizes reference identity
- could support richer metadata later
- can normalize resource references
- could allow audit events to reference a durable resource registry instead of clinical tables

Disadvantages:

- introduces an extra abstraction too early
- requires lifecycle rules for the generic resource table
- does not directly support current use-case better than Option B
- may become speculative architecture

Decision:

Rejected for now.

Can be reconsidered later if audit, search, or resource registry needs become more complex.

---

### Option D: Store the whole audited entity reference as JSON

Example:

    entity JSONB

Advantages:

- flexible
- easy to add fields
- can mimic FHIR-like reference structures

Disadvantages:

- weaker relational clarity
- weaker constraints
- less explicit indexing
- easier to misuse
- unnecessary for the current shape

Decision:

Rejected.

The current reference shape is simple enough for explicit columns.

---

### Option E: Model `agent` as an enum or catalog

Example enum:

    AuditAgent.SYSTEM
    AuditAgent.ADMIN
    AuditAgent.USER

Example table:

    audit_agents

Advantages:

- stronger normalization
- easier to validate a small fixed set
- potential future reporting benefits

Disadvantages:

- real agents are dynamic
- authentication has not been introduced yet
- no user/actor model exists yet
- premature coupling to a future security model
- conflicts with the current domain design where `agent` is a required free-form string

Decision:

Rejected for Phase 3.

The agent should remain a required free-form string supplied by trusted runtime context.

---

### Option F: Add entity lookup index immediately

Example index:

    ix_audit_events_entity(entity_resource_type, entity_id)

Advantages:

- prepares likely future audit-by-resource queries
- useful for admin/security views
- cheap to define now

Disadvantages:

- current use-case does not filter by entity
- adds write/storage overhead before concrete need
- inconsistent with the Phase 3 index discipline used for clinical resources
- can be added later through a small migration

Decision:

Rejected for the initial Sub-issue F.

Track as:

    BACKLOG / EXPAND / P3+ / Add entity-based audit event lookup index

---

### Option G: Expand AuditAction immediately with write actions

Example values:

    create
    update
    delete

Advantages:

- prepares the enum for future clinical write use-cases
- avoids another migration soon if writes are introduced quickly
- gives a more complete audit taxonomy earlier

Disadvantages:

- no current write-side clinical use-case exists
- creates database allowed values not yet used by the application
- expands the domain ahead of actual behavior
- risks designing speculative audit semantics

Decision:

Rejected for the initial Sub-issue F.

Track as:

    BACKLOG / EXPAND / P3+ / Extend AuditAction for clinical write operations

---

## Consequences

### Positive consequences

- The audit schema remains simple and explicit.
- The table supports recent audit event listing.
- Audit events can refer to multiple resource types.
- Audit records are not automatically deleted with clinical resources.
- Audit records do not block deletion of clinical resources.
- `recorded_at` remains clearly separate from `created_at`.
- The model avoids misleading `updated_at` semantics.
- `action` is protected by a database check constraint.
- `agent` remains flexible enough for future authentication/system identities.
- The schema remains infrastructure-only and does not contaminate domain/application layers.
- Future audit enforcement can build on this schema without requiring immediate middleware or auth work.

---

### Negative consequences

- The database does not enforce that `entity_id` exists in the corresponding resource table.
- Entity reference validity must be maintained by application/infrastructure code.
- Future entity-based joins may require conditional logic.
- Entity-based lookup may require a later index migration.
- Future write actions will require a new domain and database constraint change.
- If audit requirements become stricter, the schema may need hardening.
- Not using `updated_at` means this table intentionally differs from other top-level ORM-managed tables.
- Not modeling `agent` as a foreign key means agent identity consistency depends on future trusted runtime context.

---

### Mitigations

- Add a check constraint for allowed `entity_resource_type` values.
- Add a check constraint for allowed `action` values.
- Add a check constraint preventing blank `agent` values.
- Add ORM model tests for required columns, constraints, and indexes.
- Keep audit write enforcement out of this sub-issue.
- Add mappers later to translate `AuditEventRecord` into domain `AuditEvent`.
- Add SQLAlchemy adapters later to implement audit listing ports.
- Introduce trusted agent sourcing when authentication/runtime wiring exists.
- Revisit audit write enforcement when authentication and authorization exist.
- Track entity-based audit lookup index as backlog.
- Track write-side audit actions as backlog.
- Document the difference between `recorded_at`, `created_at`, row timestamps, and audit events.

---

## Implementation guidance

The initial SQLAlchemy model should live in:

    apps/api/src/fhir_gateway/infrastructure/persistence/sqlalchemy/models/audit_event.py

The ORM record should be named:

    AuditEventRecord

The table should be named:

    audit_events

Expected SQLAlchemy column shape:

    id
    recorded_at
    agent
    action
    entity_resource_type
    entity_id
    created_at

The model should not use:

    TimestampMixin

because `TimestampMixin` includes `updated_at`.

The model may define `created_at` explicitly using:

    DateTime(timezone=True)
    server_default=func.now()
    nullable=False

Expected check constraints:

    ck_audit_events_action_allowed
    ck_audit_events_entity_resource_type_allowed
    ck_audit_events_agent_not_empty

Expected initial index:

    ix_audit_events_recorded_at

Deferred index:

    ix_audit_events_entity

tracked by:

    BACKLOG / EXPAND / P3+ / Add entity-based audit event lookup index

Deferred action expansion:

    create
    update
    delete

tracked by:

    BACKLOG / EXPAND / P3+ / Extend AuditAction for clinical write operations

The initial migration should be manual and reviewable.

The migration should not include:

- seed data
- triggers
- mappers
- adapters
- HTTP endpoints
- authentication
- authorization
- full audit write enforcement

---

## Relationship with ADR 0014

ADR 0014 defines the distinction between technical persistence timestamps and audit metadata.

This ADR builds on that distinction.

`created_at` is technical persistence metadata.

`recorded_at` is audit event domain data.

`AuditEvent` is not a substitute for generic row timestamps.

Generic row timestamps are not a substitute for audit trail.

The `audit_events` table intentionally does not use `updated_at` by default because audit events are append-oriented records.

---

## Future work

Future work may include:

- `AuditEventRecord` to domain `AuditEvent` mapper
- SQLAlchemy audit event reader adapter
- persistence-backed `ListAuditEventsUseCase`
- audit event creation adapter
- trusted current-agent provider
- audit event recorder service
- HTTP audit event listing endpoint
- authentication and authorization integration
- automatic audit logging for selected use-cases
- audit middleware or explicit audit service
- entity-based audit event lookup index
- clinical write audit actions
- advanced audit filtering
- audit pagination
- retention policy
- redaction strategy
- tamper-evidence strategy
- integration tests against PostgreSQL

These are intentionally outside the initial AuditEvent persistence sub-issue unless explicitly included later.

---

## Related backlog items

- BACKLOG / EXPAND / P3+ / Add entity-based audit event lookup index
- BACKLOG / EXPAND / P3+ / Extend AuditAction for clinical write operations
- BACKLOG / HARDEN / P3+ / Add database triggers for `updated_at` consistency

---

## Decision outcome

Use a dedicated `audit_events` table with logical audited entity references:

    entity_resource_type
    entity_id

Treat audit events as append-oriented records.

Use:

    recorded_at

for the audited action timestamp.

Use:

    created_at

for technical insertion timestamp.

Persist:

    agent

as a required free-form string supplied by trusted runtime context.

Persist:

    action

as a required string constrained to current `AuditAction` values.

Keep the initial action set limited to:

    read
    search
    export

Track future clinical write actions through:

    BACKLOG / EXPAND / P3+ / Extend AuditAction for clinical write operations

Do not add `updated_at` by default.

Do not use `TimestampMixin` by default.

Do not add polymorphic foreign keys in Phase 3.

Do not allow arbitrary user-controlled request input to decide `agent`.

Do not add the entity lookup index in the initial Sub-issue F.

Track the entity lookup index as:

    BACKLOG / EXPAND / P3+ / Add entity-based audit event lookup index

Do not implement the full audit write pipeline in this ADR/sub-issue.
