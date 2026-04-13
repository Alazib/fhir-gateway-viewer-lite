# ADR 0008: Phase 2 initial application-slice conventions

## Status
Accepted

## Context
Phase 2 introduces the **application layer** around the completed Phase 1 domain model.

The project will follow a **vertical-slice oriented approach**, starting with `SearchPatients` as the first application slice. Before implementing more slices, it is useful to establish a small set of baseline conventions for:
- use-case shape,
- port design,
- input/output strategy,
- and testing style.

These decisions are intentionally lightweight, but they are still architecturally relevant because they will influence the rest of Phase 2.

## Decision

### 1. Use-cases are modeled as classes with `execute()`
The initial application use-cases will be modeled as classes exposing an `execute()` method.

**Example**
- `SearchPatientsUseCase.execute(search_text: str)`

**Why**
This makes dependencies explicit, fits well with clean/hexagonal architecture, and keeps the orchestration unit easy to test.

---

### 2. Ports live in the application layer, not in the domain layer
Ports required by use-cases are defined in the **application layer**.

**Example**
- `PatientSearchReader`

**Why**
These abstractions exist because application use-cases need to retrieve or assemble data. They are not domain concepts or domain invariants by themselves.

---

### 3. The first ports should be narrow and slice-oriented
The first application ports should reflect the real need of the slice, instead of introducing broad repository abstractions too early.

**Example**
Preferred:
- `PatientSearchReader`

Not preferred as the first move:
- `PatientRepository` with many unrelated methods

**Why**
This reduces premature abstraction, keeps the first slice honest, and allows repository-like abstractions to emerge later only if repeated patterns justify them.

---

### 4. The first slice starts with simple input contracts

In highly formal architectures (such as strict Clean or Hexagonal Architecture), it is common practice to wrap input data into specialized classes called **`Commands`** (for actions that change state) or **`Queries`** (for data retrieval). This is done to standardize how data enters the Use Case, even if it is just a single search string.

**Decision:** For this initial phase, we will avoid this "object bureaucracy." If a Use Case only needs a string or a couple of integers, they will be passed as direct parameters. We will not create `Query` or `Command` classes
unless the input complexity clearly justifies it.

**Example**
**❌ Formal Approach (Deferred / Avoid for now):**
Forces the creation of an extra class just to "transport" a single string.

```python
# We have to create this class just to wrap one piece of data
class SearchPatientsQuery:
    def __init__(self, search_text: str):
        self.search_text = search_text

# The Use Case receives the "Query" object
class SearchPatientsUseCase:
    def execute(self, query: SearchPatientsQuery):
        # We have to unpack the data
        text = query.search_text
        ...


**✅  Preferred initial contract:
class SearchPatientsUseCase:
    # The Use Case receives the primitive type (str) directly
    def execute(self, search_text: str):
        # Use the data directly
        results = self.reader.find(search_text)
        ...

**Why**
The goal is discovery speed. Creating Query classes now is "speculative engineering": we are assuming the input will be complex before it actually is. If, in the future, the search requires 10 different filters, that will be the moment to evolve toward a Query object.
---

### 5. The first slice may return domain entities directly
For the first slice, returning domain entities directly is acceptable when the result shape is still simple and semantically aligned with the use-case.

**Example**
- `tuple[Patient, ...]`

**Why**
Here we are proposing pragmatism over the pure theory of Hexagonal Architecture. --> In very strict architectures, it is said that a Use Case should never return a Domain Entity (such as Patient) to the outside world (the controller or the API); instead, it should transform it into a DTO (Data Transfer Object). But, at this stage, introducing dedicated result DTOs would add complexity without enough evidence that they are necessary.

---

### 6. Application-layer tests should use fake ports
Application use-cases should be tested with fake implementations of their ports.

**Example**
- a fake `PatientSearchReader` used by `SearchPatientsUseCase`

**Why**
This validates the dependency direction properly:
- application depends on abstractions,
- not on framework or persistence code.

It also keeps tests fast, deterministic, and focused on orchestration behavior.

---

### 7. Package structure should start minimal
The application layer should begin with a small, readable package structure.

**Example**
- `application/use_cases/`
- `application/ports/`

**Why**
This keeps the architecture understandable while still leaving room for future growth.

## Consequences

### Positive
- The first slice remains simple and readable.
- Architecture is discovered through real use-cases instead of speculative abstractions.
- Dependency direction stays explicit and testable.
- Later slices can reuse the same conventions.

### Negative / Trade-offs
- Some decisions may need revision after 2–3 slices.
- Narrow ports may later be consolidated into broader abstractions.
- Returning domain entities directly may later give way to application result models.

## Review rule
These conventions are intentionally valid for the **initial slices** of Phase 2.

They should be reassessed once the project has implemented enough slices to determine whether:
- some ports should be consolidated,
- some outputs should move to application result models,
- or some conventions should evolve.

## Alternatives considered

### 1. Start with broad generic repositories
Rejected.
This would introduce abstractions before the first slices provide evidence that they are actually stable and useful.

### 2. Start with full input/output DTO modeling
Rejected.
Too much ceremony for the first application slice.

### 3. Implement use-cases as plain functions
Considered, but not chosen.
Functions can work, but classes with `execute()` make dependencies and orchestration boundaries clearer in this project.

## Notes
This ADR is not intended to freeze Phase 2 permanently.
Its purpose is to define the **baseline conventions for the first application slices**, so the architecture grows with discipline from the start.
