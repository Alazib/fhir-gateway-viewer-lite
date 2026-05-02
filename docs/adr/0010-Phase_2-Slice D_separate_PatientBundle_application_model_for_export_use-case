# ADR 0010: Separate PatientBundle application model for export use-case

## Status

Accepted

## Context

Phase 2 is building the application layer through vertical slices.

The project already has a `PatientSummary` application model created for the `GetPatientSummary` use-case.

`PatientSummary` is an application-level composition of:

- `Patient`
- `Condition`
- `Encounter`
- `Observation`

The next interoperability slice, `ExportPatientBundle`, also needs to assemble a patient-centered set of resources.

At first, the required resource groups are structurally similar to `PatientSummary`:

- one `Patient`
- zero or more `Condition` resources
- zero or more `Encounter` resources
- zero or more `Observation` resources

This raises an architectural decision:

Should `ExportPatientBundle` reuse `PatientSummary`, or should it return a dedicated `PatientBundle` application model?

## Decision

Create a dedicated application model:

- `PatientBundle`

`ExportPatientBundleUseCase` will return:

- `PatientBundle`

It will not return:

- `PatientSummary`
- raw dictionaries
- final FHIR-like JSON
- Pydantic/API response schemas
- domain entities as an unstructured collection

Initial expected shape:

- `patient: Patient`
- `conditions: tuple[Condition, ...]`
- `encounters: tuple[Encounter, ...]`
- `observations: tuple[Observation, ...]`

## Rationale

The key design question is not whether `PatientSummary` and `PatientBundle` initially share fields.

The key design question is whether they represent the same application concept and whether they have the same reason to change.

They do not.

`PatientSummary` represents a clinical consultation/viewer-oriented composition.

`PatientBundle` represents an interoperability/export-oriented composition.

These two concepts may evolve differently.

For example, `PatientSummary` may later evolve toward:

- clinical highlights
- active conditions
- latest observations
- timeline-oriented grouping
- UI-friendly summary sections
- future grounded AI summary inputs

`PatientBundle` may later evolve toward:

- bundle type
- generated timestamp
- resource count
- export profile
- included resource metadata
- bundle entries
- FHIR-like serialization boundaries

Reusing `PatientSummary` for export would create semantic coupling between two use-cases with different intentions.

A future change made for the viewer could accidentally affect export behavior, or a future export requirement could pollute the clinical summary model.

Therefore, a small amount of deliberate structural duplication is accepted to preserve clear application boundaries and independent evolution.

## Consequences

### Positive

- `GetPatientSummary` and `ExportPatientBundle` remain semantically distinct.
- The code communicates intent clearly.
- Future viewer-oriented changes to `PatientSummary` will not accidentally affect export behavior.
- Future export-oriented changes to `PatientBundle` will not pollute the clinical summary model.
- The application layer remains strongly typed and evidence-friendly.
- The future API/serialization layer can transform `PatientBundle` into FHIR-like JSON without forcing JSON concerns into the application model.

### Negative / Trade-offs

- `PatientBundle` initially duplicates part of the structure of `PatientSummary`.
- There will be two application models with similar fields in the short term.
- Tests will partially overlap in validation logic and normalization behavior.

This duplication is considered acceptable because it is deliberate semantic duplication, not accidental copy-paste reuse.

## Alternatives considered

### 1. Reuse `PatientSummary`

Rejected.

Although this avoids duplication in the short term, it couples clinical consultation output to interoperability export output.

This would make the meaning of `PatientSummary` too broad and could cause future changes in one use-case to affect the other.

### 2. Rename `PatientSummary` to a generic shared model such as `PatientClinicalSnapshot`

Rejected for now.

This could be a reasonable future refactor if repeated slices prove that a neutral shared clinical snapshot abstraction is needed.

However, introducing that abstraction now would require renaming existing files, tests, imports, and documentation before there is enough implementation pressure to justify it.

### 3. Return raw dictionaries or final FHIR-like JSON

Rejected.

A dictionary would weaken typing and make the application contract fragile.

Final FHIR-like JSON belongs to the future API/serialization adapter, not to the application use-case.

The application layer should decide which resources belong to the export bundle, not how the HTTP JSON response is formatted.

### 4. Create a broad `PatientBundleReader`

Rejected.

This would hide bundle composition behind a port and likely move application orchestration into infrastructure.

The use-case should orchestrate resource retrieval through existing narrow reader ports.

## Notes

This ADR does not claim that `PatientBundle` is an official FHIR Bundle representation.

At this phase, `PatientBundle` is an application model that preserves structured resources for later serialization.

FHIR-like JSON formatting, API schemas, and download behavior are intentionally deferred to later phases.
