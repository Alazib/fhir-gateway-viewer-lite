# ADR 0002: HumanName presentation formatting is outside the domain

## Status
Accepted

## Context
`HumanName` supports two representations:
- Unstructured `text`
- Structured `given` + `family`

Different UIs and API representations may require different display choices:
- prefer `text`
- prefer structured format
- show both

Embedding a single "display" decision inside the Value Object would couple the domain to presentation concerns.

## Decision
`HumanName` does not implement any presentation-specific formatting method (e.g., `to_display()`).
Formatting and display decisions are handled in the presentation/mapper layer (HTTP interfaces or UI).

## Consequences
### Positive
- Domain stays presentation-agnostic (hexagonal architecture friendly).
- Different clients can choose different representations without domain changes.
- Avoids a single "canonical" display that may not fit all consumers.

### Negative / Trade-offs
- Some formatting logic is duplicated unless centralized in a mapper/presenter.
- Consumers must explicitly choose a formatting strategy.

## Alternatives considered
1. Implement `HumanName.to_display()` in the Value Object
   - Rejected: risks hard-coding UI decisions into the domain.
