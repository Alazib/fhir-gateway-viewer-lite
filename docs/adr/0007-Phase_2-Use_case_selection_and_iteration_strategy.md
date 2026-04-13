# ADR 0007: Phase 2 use-case selection and iteration strategy

## Status
Accepted

## Context
Phase 2 is intended to build the **application architecture skeleton** around the completed Phase 1 domain model.

A key architectural question is not only **which use-cases belong in Phase 2**, but also **which use-cases must belong to Iteration 1 of the MVP** and which should be intentionally deferred to later iterations.

The project could expand into many useful use-cases across:
- **CLINICAL CORE**
- **INTEROPERABILITY**
- **AUDIT / TRACEABILITY**
- **ADMINISTRATION / SUPPORT**

However, the first iteration of the MVP should not try to absorb every useful feature. That would increase complexity, delay delivery, and risk over-engineering.

The first iteration must instead contain the **smallest set of use-cases that still gives the product strong professional meaning** in terms of:
- clinical consultation,
- interoperability,
- traceability,
- architecture quality,
- and future AI-readiness.

## Decision

### ITERATION 1 (MVP) — INCLUDED USE-CASES

These are the use-cases that must exist in the **first iteration** because they define the professional identity of the product.

## CLINICAL CORE

### `SearchPatients`
**What it does**:
Searches patients using a query-oriented contract suitable for patient discovery.

**Why it is part of Iteration 1**:
Without patient search, the viewer and API lose practical usability. This is the most basic entry-point into the product.

### `GetPatientSummary`
**What it does**:
Builds a patient-centered clinical summary by aggregating:
- patient information
- conditions
- encounters
- observations

**Why it is part of Iteration 1**:
This is the central consultation use-case of the product. It is the backbone of the “mini EHR-lite viewer” concept and one of the strongest portfolio signals.

### `ListObservationsByCode`
**What it does**:
Returns observations filtered by patient and code, enabling clinically useful structured consultation.

**Why it is part of Iteration 1**:
This gives the MVP real clinical structure and supports biomarker-oriented workflows without introducing premature specialization.

## INTEROPERABILITY

### `ExportPatientBundle`
**What it does**:
Assembles a patient-centered FHIR-like export bundle from the relevant clinical resources.

**Why it is part of Iteration 1**:
This is one of the strongest interoperability signals in the whole project. It materially increases the professional value of the MVP.

## AUDIT / TRACEABILITY

### `ListAuditEvents`
**What it does**:
Returns audit events for traceability review.

**Why it is part of Iteration 1**:
The project identity explicitly includes auditability and traceability as a professional signal. A persisted audit trail without any way to consult it would leave that value only half-realized.

**Note**:
This use-case should remain tightly scoped in Iteration 1:
- minimal read/query behavior
- no advanced admin reporting
- no dashboard complexity yet

---

### Why these use-cases define Iteration 1
Together, they provide:
- **patient discovery**
- **clinical consultation**
- **structured observation access**
- **interoperable export**
- **traceability visibility**

That is enough for a first MVP iteration that is:
- professionally serious
- portfolio-strong
- aligned with the roadmap
- and still reasonably bounded

---

## DEFERRED TO LATER ITERATIONS

These use-cases are useful, but they are not mandatory for the first iteration of the MVP.

### ITERATION 2 CANDIDATES

## CLINICAL CORE

### `GetBiomarkerTrend`
**What it does**:
Returns a trend-oriented view of a biomarker across time, optimized for charting or interpretation.

**Why deferred to Iteration 2**:
In Iteration 1, the necessary underlying data is already accessible through `ListObservationsByCode`. A dedicated trend use-case is valuable, but it is a refinement rather than a foundation.

### `ListConditionsForPatient`
**What it does**:
Returns conditions for a patient in a focused, dedicated slice.

**Why deferred to Iteration 2**:
Conditions are already accessible through `GetPatientSummary`. A separate dedicated slice improves granularity, but it is not necessary for the first MVP iteration.

### `ListEncountersForPatient`
**What it does**:
Returns encounters for a patient in a focused, timeline-oriented slice.

**Why deferred to Iteration 2**:
Encounters are already part of `GetPatientSummary`. A dedicated encounter slice is useful later, especially for UI/timeline refinement, but not essential in Iteration 1.

## INTEROPERABILITY

### `GetPatientBundlePreview`
**What it does**:
Provides an inspectable/pre-export representation of the resource set that will later be exported.

**Why deferred to Iteration 2**:
Useful, but secondary to the main export behavior.

## AUDIT / TRACEABILITY

### `GetPatientAccessHistory`
**What it does**:
Returns the access history associated with a patient.

**Why deferred to Iteration 2**:
This is a valuable traceability refinement, but it is not required for the MVP as long as basic audit event listing already exists.

### `ListUserActivity`
**What it does**:
Returns access activity associated with a specific user/actor.

**Why deferred to Iteration 2**:
This is more admin/support-oriented than strictly MVP-critical.

---

### ITERATION 3 OR LATER CANDIDATES

## ADMINISTRATION / SUPPORT

### `ExportAuditReport`
**What it does**:
Exports audit-oriented data for support/admin/reporting purposes.

**Why deferred to later iterations**:
This is a useful portfolio enhancement, but not part of the first meaningful MVP.

### `GetAuditDashboardSummary`
**What it does**:
Provides an aggregated overview of audit/traceability information.

**Why deferred to later iterations**:
This is useful for admin/reporting polish, but not necessary for the first iteration of a professionally valid MVP.

---

## Consequences

### Positive
- The MVP becomes smaller, clearer, and easier to deliver.
- The first iteration still preserves the strongest professional signals of the project:
  - consultation
  - interoperability
  - traceability
  - architecture quality
- Later use-cases can be added without bloating the first delivery.
- The project gains a healthier iteration model instead of pretending that Iteration 1 must contain everything.

### Negative / Trade-offs
- Some desirable capabilities are intentionally postponed.
- Iteration 1 will not yet expose every clinically useful slice as a dedicated use-case.
- Some refined admin/audit capabilities will only appear in later iterations.

## Alternatives considered

### 1. Put all useful use-cases into Iteration 1
Rejected.
That would slow delivery, increase complexity, and weaken the “small but strong MVP” principle.

### 2. Restrict Iteration 1 to only clinical consultation and export, without audit read behavior
Rejected.
The project explicitly wants traceability as a professional signal. Therefore, a minimal audit read use-case should exist already in Iteration 1.

### 3. Push almost all specialized use-cases to later iterations
Rejected.
That would make the first iteration too weak and reduce portfolio impact.

## Notes
This ADR defines both:
- the **Phase 2 use-case selection strategy**, and
- the **Iteration 1 vs later-iterations split**.

The key rule is:

> Iteration 1 must contain the smallest set of use-cases that still gives the MVP strong clinical, interoperability, and traceability value.

Everything else should be consciously deferred, not forgotten.
