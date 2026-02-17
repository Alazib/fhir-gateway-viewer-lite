# ADR 0003: Reference.resource_type hardening strategy

## Status
Accepted (MVP decision) / To be hardened later

## Context
FHIR-like references require a target resource type and an identifier. For the MVP, we need a simple way to express typed references (e.g., `Patient/pat-001`) without introducing excessive coupling or premature constraints.

However, allowing any string for `resource_type` risks invalid references and inconsistent data.

## Decision
For the MVP, `Reference.resource_type` is a trimmed non-empty string.
In a later hardening pass, `resource_type` will be constrained using either:
- a curated allow-list of supported resource types, or
- a `ResourceType` Enum (Patient, Observation, Condition, Encounter, etc )

This hardening is tracked under Sub-issue C (Documentation + Tests) as a completion pass.

## Consequences
### Positive
- Fast MVP iteration with minimal friction.
- Still captures "typed reference" intent.

### Negative / Trade-offs
- Invalid types are possible until hardening is implemented.
- Additional validation logic will be introduced later.

## Alternatives considered
1. Enforce Enum/allow-list immediately
   - Deferred: MVP scope prioritizes iteration speed; hardening is scheduled next.
