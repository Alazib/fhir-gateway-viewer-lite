## Value Objects (Domain)

This project models key FHIR-like primitives as **Value Objects (VOs)** to enforce domain invariants early, reduce duplication, and keep entities/resources consistent. All VOs are immutable (`@dataclass(frozen=True, slots=True)`) and validate/normalize inputs in `__post_init__`.

### Error convention
Domain validation errors are raised as `DomainValidationError` with:

- `field`: `"ClassName.attribute"` (e.g., `Code.system`, `Quantity.unit`)
- `message`: a short invariant violation message (e.g., `must be a string`, `cannot be empty`)

### Shared helpers
To avoid repetitive validation code, VOs rely on:

- `type_validator(instance, attribute_name, expected_type, optional_error_message=None)`
- `normalize_string(instance, attribute_name, attribute_required=True)`

### Implemented Value Objects (MVP)

#### ResourceId
- **Purpose:** Stable identifier for resources (e.g., `pat-001`).
- **Invariants:** must be a non-empty string (trimmed).

#### Code
- **Purpose:** Terminology code triple used in clinical content (e.g., LOINC).
- **Fields:** `system`, `code`, optional `display`.
- **Invariants:** `system` and `code` must be non-empty strings (trimmed). `display` is optional; whitespace-only becomes `None`.

#### Identifier
- **Purpose:** External identifier (system + value), e.g., MRN.
- **Invariants:** `system` and `value` must be non-empty strings (trimmed).

#### HumanName
- **Purpose:** Patient/person name representation supporting structured and unstructured inputs.
- **Fields:** `given` (stored internally as a tuple), optional `family`, optional `text`.
- **Invariants (two-mode):**
  - If `text` is present (after trim), it is valid as an unstructured name.
  - If `text` is missing/empty, then `given` must contain at least one non-empty item and `family` must be non-empty.
- **Presentation note:** name rendering/formatting (text vs given+family or both) is handled in the presentation/mapper layer, not inside the VO (documented in Sub-issue C).

#### Instant
- **Purpose:** A precise timestamp for clinical events and audit records.
- **Invariants:** must be a timezone-aware `datetime`; stored normalized to UTC.

#### Period
- **Purpose:** Time interval (open or closed).
- **Fields:** optional `start`, optional `end` (both `Instant`).
- **Invariants:** if both exist, then `start <= end`.

#### Reference
- **Purpose:** Typed pointer to another resource (e.g., `Observation.subject -> Patient/pat-001`).
- **Fields:** `resource_type` (string), `id` (`ResourceId`).
- **Invariants:** `resource_type` must be a non-empty string (trimmed); `id` must be a `ResourceId`.
- **Hardening note:** `resource_type` will be constrained (allow-list or Enum) in a later hardening pass (Sub-issue C).

#### Quantity
- **Purpose:** Numeric measurement with unit (used for biomarker values, etc.).
- **Fields:** optional `value` (int/float), optional `unit` (string).
- **Invariants:** if `value` is present, `unit` must be present and non-empty (trimmed). `value` must be numeric when present.
- **Hardening note:** `unit` is currently free-form for MVP. It should be constrained in a later pass (e.g., UCUM allow-list / validation, or a curated demo allow-list aligned with biomarker scenarios).

### Next steps
This section is intentionally concise. The full rationale, edge cases, and ADR-backed decisions for each VO (including future constraints and terminology policies) are completed in **Sub-issue C (Documentation + Tests)**.
