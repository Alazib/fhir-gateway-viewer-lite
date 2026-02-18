# MVP Entity Model (FHIR-like Domain)

## Purpose and scope
This document describes the **MVP clinical domain entities** for the project (FHIR-like, framework-agnostic). It focuses on:
- what each entity represents in healthcare/FHIR terms,
- the entity attributes (types, constraints, PK/FK intent),
- the relationships between entities (ER-style, conceptual + a DB-friendly view).

> Notes: This is a **domain model** document. The **exact persistence mapping** (tables/columns, indexes, migrations) will be finalized in the persistence phase.
Identifiers are represented with `ResourceId` (string) in the domain. In a relational DB, this maps naturally to a `VARCHAR` primary key.

---

## Entities overview (clinical meaning)

| Entity | FHIR inspiration | What it represents (healthcare meaning) | Why we need it in the MVP |
|---|---|---|---|
| Patient | `Patient` | A person receiving care. Root subject for clinical data. | Anchor for timeline and all “subject” references. |
| Observation | `Observation` | A measured or asserted clinical data point (labs/vitals). | Biomarker time-series (e.g., HbA1c). |
| Condition | `Condition` | A diagnosis/problem list item (e.g., diabetes). | Timeline context and clinical status. |
| Encounter | `Encounter` | A visit/admission/contact with the healthcare system. | Timeline structure (episodes/visits). |
| AuditEvent (minimal) | `AuditEvent` | Record of access to clinical resources (who/what/when). | Professional signal: traceability / compliance foundation. |

---

## Entity attributes (domain-level + relational intent)

### Patient
**Clinical meaning:** The subject of record (the person).

| Attribute | Domain type | Required | DB column(s) (suggested) | Key / constraint intent | Notes |
|---|---|---:|---|---|---|
| `id` | `ResourceId` | Yes | `id` (VARCHAR) | **PK** | Stable identifier for the patient resource. |
| `identifier` | `Identifier \| None` | No | `identifier_system` (VARCHAR), `identifier_value` (VARCHAR) | Unique (optional) | External ID (MRN, national ID). Uniqueness may be enforced depending on use-case. |
| `name` | `HumanName \| None` | No | `name_text` (VARCHAR), `name_family` (VARCHAR), `name_given` (JSON/TEXT) | None | Domain supports structured/unstructured. Presentation formatting is outside domain. |

**Domain constraints (MVP):**
- `id` always required.
- `identifier` and `name` are optional to keep MVP flexible for partial/synthetic data.

---

### Observation (Quantity-only value in MVP)
**Clinical meaning:** A measured value at a precise time (lab/vital).
**MVP decision:** `value` is **Quantity-only** (no string/boolean/codeable concepts yet).

| Attribute | Domain type | Required | DB column(s) (suggested) | Key / constraint intent | Notes |
|---|---|---:|---|---|---|
| `id` | `ResourceId` | Yes | `id` (VARCHAR) | **PK** | Observation identifier. |
| `status` | `str` | Yes | `status` (VARCHAR) | Allow-list later | Keep simple now; later restrict to FHIR statuses. |
| `code` | `Code` | Yes | `code_system` (VARCHAR), `code_code` (VARCHAR), `code_display` (VARCHAR) | Not null on system+code | Terminology identity (e.g., LOINC). |
| `subject` | `Reference` | Yes | `patient_id` (VARCHAR) | **FK** -> Patient(id) | Domain Reference is typed; for MVP subject must be Patient. |
| `effective` | `Instant` | Yes | `effective_at` (TIMESTAMPTZ) | Not null | Stored normalized to UTC in domain; DB uses timestamptz. |
| `value` | `Quantity` | Yes | `value_num` (NUMERIC/DOUBLE), `value_unit` (VARCHAR) | Unit required if value present | MVP: numeric+unit. Future: UCUM/allow-list hardening. |

**Domain constraints (MVP):**
- Must have `code`.
- Must have `subject` referencing a `Patient`.
- Must have `effective` (timezone-aware, normalized to UTC).
- Must have `value` as Quantity.

---

### Condition
**Clinical meaning:** A diagnosis or problem list item.

| Attribute | Domain type | Required | DB column(s) (suggested) | Key / constraint intent | Notes |
|---|---|---:|---|---|---|
| `id` | `ResourceId` | Yes | `id` (VARCHAR) | **PK** | Condition identifier. |
| `code` | `Code` | Yes | `code_system`, `code_code`, `code_display` | Not null on system+code | Diagnosis code (e.g., SNOMED/ICD-like). |
| `subject` | `Reference` | Yes | `patient_id` (VARCHAR) | **FK** -> Patient(id) | MVP: must reference Patient. |
| `recorded_date` | `Instant \| None` | No | `recorded_at` (TIMESTAMPTZ) | Nullable | Useful in timeline; optional because historical data may be incomplete. |

**Domain constraints (MVP):**
- Must have `code`.
- Must have `subject` referencing a `Patient`.

---

### Encounter
**Clinical meaning:** A visit/admission/contact (episode/visit container).

| Attribute | Domain type | Required | DB column(s) (suggested) | Key / constraint intent | Notes |
|---|---|---:|---|---|---|
| `id` | `ResourceId` | Yes | `id` (VARCHAR) | **PK** | Encounter identifier. |
| `subject` | `Reference` | Yes | `patient_id` (VARCHAR) | **FK** -> Patient(id) | MVP: must reference Patient. |
| `period` | `Period \| None` | No | `start_at` (TIMESTAMPTZ), `end_at` (TIMESTAMPTZ) | start <= end (when both) | Period is open/closed; coherence enforced by `Period`/`Instant`. |

**Domain constraints (MVP):**
- Must have `subject` referencing a `Patient`.
- If `period` exists and both bounds exist: start <= end.

---

### AuditEvent (minimal)
**Clinical meaning:** A record that someone/something accessed a clinical resource.

| Attribute | Domain type | Required | DB column(s) (suggested) | Key / constraint intent | Notes |
|---|---|---:|---|---|---|
| `id` | `ResourceId` | Yes | `id` (VARCHAR) | **PK** | AuditEvent identifier. |
| `recorded` | `Instant` | Yes | `recorded_at` (TIMESTAMPTZ) | Not null | Normalized to UTC. |
| `agent` | `str` | Yes | `agent` (VARCHAR) | Not null | MVP: user/service identifier (later: structured agent). |
| `action` | `str` | Yes | `action` (VARCHAR) | Not null | MVP: string (later: allow-list). |
| `entity` | `Reference` | Yes | `entity_type` (VARCHAR), `entity_id` (VARCHAR) | Polymorphic reference | Points to the accessed resource (Patient/Observation/etc.). |

**Domain constraints (MVP):**
- `recorded` required.
- `entity` required.
- `entity` is a typed reference (future hardening: restrict allowed resource types).

---

## Relationships (ER-style)

### Conceptual relationships (domain)
- **Patient 1 — N Observation**
  - Observation.subject must reference Patient
- **Patient 1 — N Condition**
  - Condition.subject must reference Patient
- **Patient 1 — N Encounter**
  - Encounter.subject must reference Patient
- **AuditEvent N — 1 (polymorphic) Entity**
  - AuditEvent.entity references *one* resource (Patient/Observation/Condition/Encounter, etc.)

### Relationship table (database-friendly view)
| From | To | Cardinality | FK / join fields | Notes |
|---|---|---|---|---|
| Observation | Patient | N:1 | `observation.patient_id -> patient.id` | Derived from `Reference(subject)` in domain. |
| Condition | Patient | N:1 | `condition.patient_id -> patient.id` | Derived from `Reference(subject)` in domain. |
| Encounter | Patient | N:1 | `encounter.patient_id -> patient.id` | Derived from `Reference(subject)` in domain. |
| AuditEvent | Any resource | N:1 | `(audit_event.entity_type, audit_event.entity_id)` | Polymorphic association; hardening later. |

---

## Constraints and future hardening (tracked)
- **Reference.resource_type**: currently any non-empty string; must be hardened later (Enum or allow-list).
- **Quantity.unit**: currently free-form string; should be hardened later (UCUM validation or curated allow-list).
- **Terminology**: `Code.system+code` can be constrained later via curated allow-list for demo scenarios (domain-level).
- **Status fields**: `Observation.status` is string in MVP; later restrict to a small allow-list aligned with FHIR statuses.

---

## Summary
This MVP entity model is intentionally minimal but clinically meaningful:
- Patient anchors the record,
- Observation provides measurable time-series data,
- Condition and Encounter provide timeline context,
- AuditEvent adds a compliance-grade professional signal.

The model is designed to be **framework-agnostic**, testable, and extensible toward stricter terminology and unit constraints in later iterations.
