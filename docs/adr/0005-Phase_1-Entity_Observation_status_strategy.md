# ADR 0005: Observation.status modeling strategy

## Status
Accepted

## Context
`Observation.status` is not a free-text field. In FHIR, it is a constrained lifecycle/status attribute with a defined set of allowed values.

For this project, Observation is a core entity used for clinical timeline display and biomarker series. Leaving `status` as a raw string would allow invalid values, increase normalization logic, and weaken domain consistency.

At the same time, this MVP does not yet model workflow transitions (e.g., register -> preliminary -> final), so a full state machine would introduce unnecessary complexity.

## Decision
`Observation.status` is modeled as a domain enum:

- `registered`
- `preliminary`
- `final`
- `amended`
- `corrected`
- `cancelled`
- `entered-in-error`
- `unknown`

Implementation uses a `str, Enum` type (`ObservationStatus`) so the domain receives a constrained semantic value rather than a free-form string, while still remaining convenient for API serialization and boundary-layer mapping.

The conversion from transport-layer string values to `ObservationStatus` is expected to happen at the boundary layer (e.g., HTTP schemas/mappers or UI integration layer). The domain validates that the final value is a valid enum member.

## Status meanings and examples

### `registered`
The observation has been registered or ordered, but no actual result is available yet.

**Example:**
A laboratory HbA1c observation record is created when the test is ordered, but the sample has not yet been processed.

### `preliminary`
A result is available, but it is still provisional and not yet finalized.

**Example:**
A lab system returns an early glucose result before final validation by the laboratory workflow.

### `final`
The result is complete and considered the definitive clinically usable version.

**Example:**
An HbA1c result has been reviewed and released as the final laboratory result shown to the clinician.

### `amended`
A previously final result has been updated or supplemented, but not necessarily because it was wrong.

**Example:**
Additional interpretive information is added to a previously final observation without changing the core result value.

### `corrected`
A previously issued result has been corrected because the earlier version was inaccurate.

**Example:**
A potassium result was released incorrectly due to a processing issue and is later corrected with a new definitive value.

### `cancelled`
The observation workflow was cancelled and no valid result will be produced.

**Example:**
A test order is cancelled because the sample was never collected or the request was withdrawn.

### `entered-in-error`
The observation resource was created in error and must not be used clinically.

**Example:**
An observation was accidentally recorded for the wrong patient and is later marked as entered in error.

### `unknown`
The system does not know the real status of the observation.

**Example:**
Legacy or imported data is received without enough metadata to determine whether the result was preliminary, final, or corrected.

## Consequences

### Positive
- Stronger domain consistency.
- No string trimming/normalization needed for `status` inside the entity.
- Better alignment with FHIR semantics.
- Better fit for API serialization and schema generation.
- Lower risk of invalid or inconsistent status values in stored resources.

### Negative / Trade-offs
- Slightly stricter API/domain boundary handling: string inputs must be mapped to enum values.
- More statuses than strictly required for a minimal biomarker demo.
- No transition rules are enforced yet.

## Alternatives considered

### 1. Keep `status` as free-form string
Rejected.
This weakens the domain model and pushes too much responsibility to UI/boundary normalization.

### 2. Use a reduced custom MVP allow-list
Considered, but not chosen.
Although possible, the cost of keeping the full FHIR-inspired set is very low and provides better semantic alignment.

### 3. Implement a full state machine
Deferred.
A state machine only becomes justified when the system explicitly models Observation lifecycle transitions through application commands/use-cases. That is not part of the current MVP scope.

## Notes
This ADR only constrains valid status membership. It does **not** define allowed status transitions. If workflow transition rules become relevant in a later phase, they should be documented in a dedicated ADR.
