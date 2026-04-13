# ADR 0006: AuditEvent modeling strategy

## Status
Accepted

## Context
This project includes a minimal `AuditEvent` domain entity to represent traceability of access to clinical resources. Even in a small MVP, auditability is an important professional signal in health-oriented software because access to patient-related information should be attributable and reviewable.

The project is currently consultation-oriented (viewer + API access to synthetic records), not a full transactional clinical system. Therefore, the MVP audit model should remain small and focused on access events rather than full operational provenance.

Two design questions must be resolved:

1. Should `action` be free-form text or a constrained set of values?
2. Should `agent` also be constrained as an enum?

## Decision

### 1. `AuditEvent.action` is modeled as a constrained enum
We model `action` as a `str, Enum` with a small closed set aligned with the current MVP scope:

- `read`
- `search`
- `export`

This is preferred over a free-form string because audit actions are system-defined categories, not arbitrary user text.

### 2. `AuditEvent.agent` remains a normalized non-empty string
We do **not** model `agent` as an enum.

`agent` identifies who or what performed the action (for example, a username, service account, or job name). That is not a small stable catalog and should not be constrained as if it were one.

If later the system needs to distinguish categories of actors, that should be modeled separately with a field such as `agent_type` (for example, `human-user`, `service`, `batch-job`), while `agent` itself should still carry the concrete identifier.

## Meaning of each action and examples

### `read`
A specific clinical resource is accessed directly for viewing or retrieval.

**Example:**
A clinician opens a patient's HbA1c observation in the EHR-lite viewer.

### `search`
A query is executed to discover or list matching clinical resources.

**Example:**
A user searches for patients by identifier or lists all observations for a patient.

### `export`
Clinical data is packaged and delivered outside the normal on-screen reading flow.

**Example:**
A patient summary or FHIR-like Bundle JSON is exported from the API.

## Why these actions and not more?
The current MVP is focused on consultation and export, not on write-heavy clinical workflows. Therefore, the enum intentionally stays small.

Actions such as `create`, `update`, or `delete` are plausible in a broader system, but they are not necessary for the current project scope. If the application later supports write operations, the enum can be extended in a dedicated change.

## Consequences

### Positive
- Stronger consistency in audit records.
- No arbitrary action strings such as `open`, `viewed`, `downloaded`, `see`, etc.
- Better alignment between audit data and real use-cases in this MVP.
- Easier future reporting and filtering by audit action.

### Negative / Trade-offs
- Boundary layers must map incoming action strings to enum values.
- The initial enum is intentionally narrow and may need to evolve if the application scope expands.

## Alternatives considered

### 1. Keep `action` as a free-form string
Rejected.
This weakens consistency and makes audit analysis noisier.

### 2. Model both `action` and `agent` as enums
Rejected.
`action` is a system category; `agent` is a concrete actor identifier. They are not the same kind of data.

### 3. Introduce `agent_type` in this MVP
Deferred.
Useful, but not necessary for the current minimal audit scope.

## Notes
This ADR defines the minimal semantic shape of `AuditEvent` in the domain. It does not define persistence, retention policies, or security reporting workflows. Those belong to later phases.
