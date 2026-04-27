# ADR 0009: Patient summary output model and narrow reader ports

## Status
Accepted

## Context
The `GetPatientSummary` slice is the first Phase 2 use-case that composes several clinical resources into a meaningful application-level result.

Unlike `SearchPatients`, which can return `Patient` entities directly, `GetPatientSummary` does not represent a single domain entity. It represents an application-level composition of:

- one `Patient`
- zero or more `Condition` resources
- zero or more `Encounter` resources
- zero or more `Observation` resources

This raises two architectural questions:

1. Should the use-case return raw domain resources, a dictionary, an API DTO, or an application result model?
2. Should the use-case depend on one broad `PatientSummaryReader` port or on several narrower resource-oriented reader ports?

These decisions are important because the patient summary will later support:

- the patient summary API endpoint,
- the EHR-lite viewer,
- clinical timeline rendering,
- future grounded AI summaries and Q&A,
- and evidence-preserving application flows.

## Decision

### 1. `GetPatientSummary` returns an application result model

The use-case will return a dedicated application-level result model, tentatively named:

- `PatientSummary`

Expected shape:

- `patient: Patient`
- `conditions: tuple[Condition, ...]`
- `encounters: tuple[Encounter, ...]`
- `observations: tuple[Observation, ...]`

This result model belongs to the **application layer**, not to the domain layer and not to the API layer.

## Why

A patient summary is not a single domain entity. It is an application-level composition of several domain resources.

Returning a structured application result model keeps the use-case output:

- explicit,
- type-safe,
- easy to test,
- suitable for API serialization later,
- suitable for viewer consumption later,
- and suitable for future grounded AI features.

## Example

Preferred:

- `PatientSummary(patient=patient, conditions=..., encounters=..., observations=...)`

Not preferred:

- `dict[str, Any]`
- plain text summary
- FHIR-like Bundle
- API/Pydantic response schema

## Rationale

A plain dictionary would weaken typing and make the result fragile.

A natural-language text summary would be premature and would mix application orchestration with presentation/AI generation.

A FHIR-like Bundle belongs to the `ExportPatientBundle` use-case, not to `GetPatientSummary`.

A Pydantic/API response schema belongs to the future API adapter layer, not to the application core.

---

### 2. The result must remain evidence-friendly

The summary output must preserve structured clinical evidence.

That means it should keep:

- resource identity,
- resource grouping,
- timestamps,
- codes,
- quantities,
- references,
- and original domain resource structure.

## Why

Future AI Engineering features must be grounded in structured evidence rather than free text.

For example, a future AI-generated summary should be able to trace its statements back to concrete resources such as:

- `Observation obs-001`
- `Condition con-001`
- `Encounter enc-001`

Therefore, `GetPatientSummary` should not flatten the result into a narrative too early.

---

### 3. `GetPatientSummary` depends on several narrow reader ports

The use-case will depend on several reader ports instead of a single broad `PatientSummaryReader`.

Initial ports:

- `PatientReader`
- `ConditionReader`
- `EncounterReader`
- `ObservationReader`

Expected responsibilities:

- `PatientReader`: retrieve the target patient
- `ConditionReader`: list conditions for a patient
- `EncounterReader`: list encounters for a patient
- `ObservationReader`: list observations for a patient

## Why

The application layer should own the orchestration of the patient summary.

If a single `PatientSummaryReader` returned the full summary, the composition logic would be hidden behind the port and likely pushed into infrastructure. That would make the use-case too thin and would blur the responsibility boundary between application and infrastructure.

With narrow reader ports:

- the use-case clearly expresses its orchestration,
- each port has one focused responsibility,
- infrastructure remains responsible only for data retrieval,
- and the application layer remains responsible for composing the result.

## Example

Preferred:

- `patient_reader.get_by_id(patient_id)`
- `condition_reader.list_by_patient(patient_id)`
- `encounter_reader.list_by_patient(patient_id)`
- `observation_reader.list_by_patient(patient_id)`
- application use-case builds `PatientSummary`

Not preferred:

- `patient_summary_reader.get_summary(patient_id)`
- infrastructure builds and returns `PatientSummary`

---

### 4. The ports are still narrow and read-oriented, not generic repositories

The selected ports should not become broad CRUD-style repositories.

They should expose only the read operations required by this slice and nearby future slices.

## Why

Phase 2 follows a vertical-slice approach. Abstractions should be discovered from real use-cases rather than invented too early.

For example, this phase does not need:

- `save`
- `delete`
- `update`
- `list_all`

Therefore, broad repository abstractions are intentionally avoided unless repeated usage later proves they are justified.

---

### 5. Missing patient is an application-level not-found case

If the requested patient does not exist, `GetPatientSummary` should raise an application-level not-found error.

Expected error:

- `ApplicationNotFoundError`

## Why

Requesting a summary for a non-existing patient is not a domain invariant violation. It is an application use-case failure.

This distinction also prepares the future API layer for clean HTTP mapping:

- validation error -> `400 Bad Request`
- not found error -> `404 Not Found`

## Consequences

### Positive
- The patient summary remains structured and evidence-friendly.
- The use-case owns orchestration instead of hiding it in infrastructure.
- Ports remain focused and easy to test.
- Future API, viewer, and AI features can reuse the same application result shape.
- The design avoids premature generic repositories.

### Negative / Trade-offs
- The use-case constructor will need several dependencies.
- More ports must be defined than with a single `PatientSummaryReader`.
- If many slices later repeat the same access patterns, some ports may need to be consolidated.

## Alternatives considered

### 1. Return a plain dictionary
Rejected.

A dictionary is flexible but weakly typed and fragile. It would make the application contract less explicit.

### 2. Return a natural-language patient summary
Rejected.

Natural-language generation belongs to a later presentation or AI layer. The application use-case should preserve structured evidence.

### 3. Return a FHIR-like Bundle
Rejected.

Bundle export is a separate interoperability use-case and belongs to `ExportPatientBundle`.

### 4. Use a single `PatientSummaryReader`
Rejected.

This would hide the composition logic behind a port and likely push application orchestration into infrastructure.

### 5. Use broad generic repositories immediately
Rejected.

This would introduce methods and responsibilities before the vertical slices prove they are needed.

## Notes
This ADR applies specifically to the `GetPatientSummary` slice and establishes a pattern for structured, evidence-friendly application result models.

The decision may be revisited after several slices if repeated access patterns justify consolidation of ports or introduction of broader repository-like abstractions.
