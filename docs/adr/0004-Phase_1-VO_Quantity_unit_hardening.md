# ADR 0004: Quantity.unit validation strategy (MVP free-form, harden later)

## Status
Accepted (MVP decision) / To be hardened later

## Context
`Quantity` represents measured numeric values with units (e.g., HbA1c %, glucose mg/dL). In healthcare interoperability, units are commonly standardized using UCUM. However, enforcing UCUM from day one adds scope and tooling complexity (validation tables, parsing, edge cases) that is disproportionate for the MVP.

At the same time, allowing arbitrary unit strings can lead to inconsistent data (e.g., "mg/dl" vs "mg/dL", "%" vs "percent") and makes downstream aggregation/comparison harder.

## Decision
For the MVP:
- `Quantity.unit` is treated as a trimmed string.
- If `Quantity.value` is present, `Quantity.unit` must also be present and non-empty.
- No standardized unit validation is enforced in the domain at this stage.

For a later hardening pass:
- Constrain `unit` using either:
  1) a curated allow-list aligned with demo biomarker scenarios (e.g., `%`, `mg/dL`, `mmol/L`), and/or
  2) UCUM validation (preferred long-term direction).

Hardening is tracked for Sub-issue C (Documentation + Tests) or the next iteration, depending on scope.

## Consequences
### Positive
- Keeps MVP scope focused and iteration speed high.
- Still enforces the critical invariant: a numeric value must not exist without a unit.
- Avoids premature complexity (UCUM parsing/validation) before it is needed.

### Negative / Trade-offs
- Unit strings can be inconsistent until hardening is implemented.
- Consumers (UI/mappers) may need temporary normalization rules (e.g., casing conventions).

## Alternatives considered
1. Enforce UCUM validation immediately
   - Rejected for MVP: increases scope significantly and requires additional validation resources.
2. Enforce a strict allow-list immediately
   - Deferred: acceptable but still introduces maintenance overhead; better informed after defining demo scenarios.
