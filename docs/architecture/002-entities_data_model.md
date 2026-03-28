# MVP Entity Model (FHIR-like Domain)

## Purpose and scope
This document describes the **MVP clinical domain entities** for the project (FHIR-like, framework-agnostic). It focuses on:
- what each entity represents in healthcare/FHIR terms,
- the entity attributes (types, constraints, PK/FK intent),
- the relationships between entities (ER-style, conceptual + a DB-friendly view).

> Notes: This is a **domain model** document. The **exact persistence mapping** (tables, indexes, constraints, migrations) will be finalized in the persistence phase.
> `ResourceId` is modeled as a string-based identifier in the domain. In the relational model, that maps naturally to a `VARCHAR` primary key.
> The “DB column(s) (suggested)” sections below are intentionally concrete enough to guide the persistence phase, but they are still **proposed mappings**, not final DDL.

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
| `id` | `ResourceId` | Yes | `patient.id VARCHAR` | **PK** | Stable identifier for the patient resource. |
| `identifiers` | `tuple[Identifier, ...]` | No | Child table: `patient_identifier(patient_id, system, value)` | FK `patient_id -> patient.id`; unique at least on `(patient_id, system, value)` | 0..* external identifiers (MRN, national id, insurer id). Domain prevents duplicates within the same Patient. A stronger uniqueness policy on `(system, value)` can be decided later if needed. |
| `name` | `HumanName \| None` | No | `patient.name_text VARCHAR NULL`, `patient.name_family VARCHAR NULL`, `patient.name_given JSONB/TEXT NULL` | None | Domain supports structured/unstructured name input. Presentation formatting is outside the domain. |

**Domain constraints (MVP):**
- `id` always required.
- `identifiers` and `name` are optional to keep MVP flexible for partial/synthetic data.
- `identifiers` must not contain duplicates (same `(system, value)` within the same Patient).

---

### Observation (Quantity-only value in MVP)
**Clinical meaning:** A measured value at a precise time (lab/vital).
**MVP decision:** `value` is **Quantity-only** (no string/boolean/codeable concepts yet).

| Attribute | Domain type | Required | DB column(s) (suggested) | Key / constraint intent | Notes |
|---|---|---:|---|---|---|
| `id` | `ResourceId` | Yes | `observation.id VARCHAR` | **PK** | Observation identifier. |
| `status` | `ObservationStatus` | Yes | `observation.status VARCHAR` | Not null; candidate DB `CHECK` constraint or DB enum in persistence phase | Domain models status as a constrained enum, stored relationally as text. |
| `code` | `Code` | Yes | `observation.code_system VARCHAR`, `observation.code_code VARCHAR`, `observation.code_display VARCHAR NULL` | Not null on `code_system` + `code_code` | Terminology identity (e.g., LOINC). |
| `subject` | `Reference` | Yes | `observation.patient_id VARCHAR` | **FK** -> `patient.id` | Domain uses a typed `Reference`, but in this MVP `Observation.subject` is constrained to `Patient`, so the relational model can store a direct patient FK. |
| `effective` | `Instant` | Yes | `observation.effective_at TIMESTAMPTZ` | Not null | Stored normalized to UTC in the domain; DB should persist timezone-aware timestamps. |
| `value` | `Quantity` | Yes | `observation.value_num NUMERIC`, `observation.value_unit VARCHAR` | Not null for both in MVP | MVP: numeric + unit only. Future hardening: UCUM or curated allow-list. |

**Domain constraints (MVP):**
- Must have `code`.
- Must have `status` as a valid `ObservationStatus`.
- Must have `subject` referencing a `Patient`.
- Must have `effective` (timezone-aware, normalized to UTC).
- Must have `value` as `Quantity`.

---

### Condition
**Clinical meaning:** A diagnosis or problem list item.

| Attribute | Domain type | Required | DB column(s) (suggested) | Key / constraint intent | Notes |
|---|---|---:|---|---|---|
| `id` | `ResourceId` | Yes | `condition.id VARCHAR` | **PK** | Condition identifier. |
| `code` | `Code` | Yes | `condition.code_system VARCHAR`, `condition.code_code VARCHAR`, `condition.code_display VARCHAR NULL` | Not null on `code_system` + `code_code` | Diagnosis code (e.g., SNOMED/ICD-like). |
| `subject` | `Reference` | Yes | `condition.patient_id VARCHAR` | **FK** -> `patient.id` | Domain uses `Reference`, but `Condition.subject` is constrained to `Patient` in MVP. |
| `recorded_date` | `Instant \| None` | No | `condition.recorded_at TIMESTAMPTZ NULL` | Nullable | Useful in timeline; optional because historical data may be incomplete. |

**Domain constraints (MVP):**
- Must have `code`.
- Must have `subject` referencing a `Patient`.

---

### Encounter
**Clinical meaning:** A visit/admission/contact (episode/visit container).

| Attribute | Domain type | Required | DB column(s) (suggested) | Key / constraint intent | Notes |
|---|---|---:|---|---|---|
| `id` | `ResourceId` | Yes | `encounter.id VARCHAR` | **PK** | Encounter identifier. |
| `subject` | `Reference` | Yes | `encounter.patient_id VARCHAR` | **FK** -> `patient.id` | Domain uses `Reference`, but `Encounter.subject` is constrained to `Patient` in MVP. |
| `period` | `Period` | Yes | `encounter.start_at TIMESTAMPTZ`, `encounter.end_at TIMESTAMPTZ NULL` | `start_at` not null; `end_at` nullable; `start_at <= end_at` when `end_at` exists | `Period` is required in MVP. `start_at` is mandatory for timeline placement; `end_at` remains optional for ongoing/open encounters. |

**Domain constraints (MVP):**
- Must have `subject` referencing a `Patient`.
- Must have `period`.
- `period.start` is required.
- `period` must be coherent (`start <= end` when `end` exists).

---

### AuditEvent (minimal)
**Clinical meaning:** A record that someone/something accessed a clinical resource.

| Attribute | Domain type | Required | DB column(s) (suggested) | Key / constraint intent | Notes |
|---|---|---:|---|---|---|
| `id` | `ResourceId` | Yes | `audit_event.id VARCHAR` | **PK** | AuditEvent identifier. |
| `recorded` | `Instant` | Yes | `audit_event.recorded_at TIMESTAMPTZ` | Not null | Normalized to UTC. |
| `agent` | `str` | Yes | `audit_event.agent VARCHAR` | Not null | MVP: user/service identifier. Can be modeled later as a richer structure. |
| `action` | `str` | Yes | `audit_event.action VARCHAR` | Not null | MVP: string. A constrained allow-list can be introduced later. |
| `entity` | `Reference` | Yes | `audit_event.entity_type VARCHAR`, `audit_event.entity_id VARCHAR` | Composite polymorphic reference; candidate composite index on `(entity_type, entity_id)` | Points to the accessed resource (Patient/Observation/Condition/Encounter, etc.). |

**Domain constraints (MVP):**
- `recorded` required.
- `entity` required.
- `entity` is a typed reference (future hardening: restrict allowed resource types).

---

## Relationships (ER-style)

### Conceptual relationships (domain)
- **Patient 1 — N Observation**
  - `Observation.subject` must reference `Patient`
- **Patient 1 — N Condition**
  - `Condition.subject` must reference `Patient`
- **Patient 1 — N Encounter**
  - `Encounter.subject` must reference `Patient`
- **Patient 1 — N PatientIdentifier**
  - `Patient.identifiers` is a multi-valued attribute modeled relationally as a child table
- **AuditEvent N — 1 (polymorphic) Entity**
  - `AuditEvent.entity` references one resource (`Patient`, `Observation`, `Condition`, `Encounter`, etc.)

### Relationship table (database-friendly view)
| From | To | Cardinality | FK / join fields | Notes |
|---|---|---|---|---|
| `observation` | `patient` | N:1 | `observation.patient_id -> patient.id` | Derived from `Reference(subject)` in the domain. |
| `condition` | `patient` | N:1 | `condition.patient_id -> patient.id` | Derived from `Reference(subject)` in the domain. |
| `encounter` | `patient` | N:1 | `encounter.patient_id -> patient.id` | Derived from `Reference(subject)` in the domain. |
| `patient_identifier` | `patient` | N:1 | `patient_identifier.patient_id -> patient.id` | Normalized storage for `Patient.identifiers`. |
| `audit_event` | any resource | N:1 | `(audit_event.entity_type, audit_event.entity_id)` | Polymorphic association; hardening later. |

---

## Constraints and future hardening (tracked)
- **Reference.resource_type**: currently any non-empty string in the VO; should be hardened later (Enum or allow-list).
- **Quantity.unit**: currently free-form string; should be hardened later (UCUM validation or curated allow-list).
- **Observation.status**: already constrained in the domain via `ObservationStatus`; persistence phase may choose DB enum or `CHECK` constraint.
- **Terminology**: `Code.system + code` can be constrained later via curated allow-list for demo scenarios (domain-level).
- **AuditEvent.action**: currently free-form string in MVP; may later become an allow-list or enum.

---

## Summary
This MVP entity model is intentionally small but clinically meaningful:
- `Patient` anchors the record,
- `Observation` provides measurable time-series data,
- `Condition` and `Encounter` provide timeline context,
- `AuditEvent` adds a compliance-oriented traceability signal.

The model is designed to be **framework-agnostic**, testable, and easy to project into a relational schema during the persistence phase.
