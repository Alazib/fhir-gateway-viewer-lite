# FHIR Mini-Gateway + EHR-lite Viewer + Applied AI Engineering — Roadmap

## 1. Project overview

This repository implements a small, portfolio-grade Health IT application composed of:

- a **FHIR-like API (mini gateway)** exposing a deliberately scoped subset of clinical resources, and
- an **EHR-lite viewer (mini visor)** focused on patient navigation, clinical timeline exploration, and basic biomarker trend visualization.

The project is also intentionally designed to evolve into a strong **Applied AI Engineering** portfolio case on top of structured synthetic clinical data.

The goal is to demonstrate:

- **interoperability-oriented backend engineering**
- **clean architecture and strong domain modeling**
- **professional documentation and ADR discipline**
- **testing and reproducibility**
- and later, **grounded, evaluable AI engineering** over structured health data

This application is intentionally designed to remain small, iterative, and easy to evaluate by a reviewer, while still showcasing depth in:

- architecture
- modeling
- documentation
- software quality
- and AI engineering readiness

### 1.1 Why this is healthcare/biotech-specific

This project is not a generic CRUD demo.

It is built around common healthcare integration concerns:

- **Resource-oriented clinical modeling** (`Patient`, `Observation`, `Condition`, `Encounter`, `AuditEvent`)
- **Semantic coding** through clinical codes for observations and conditions, avoiding “free-text-only” clinical data
- **Traceability** through audit events and role-based access patterns typically expected in regulated environments
- **Synthetic data only**: no real patient data is used; the project is intended to rely on reproducible demo data and fixtures

### 1.2 Why this is also an AI Engineering project

This project is not meant to become “just a chatbot on top of data”.

It is intended to become a serious **Applied AI Engineering** case by building AI features on top of:

- structured clinical resources
- reproducible synthetic datasets
- explicit grounding
- auditable outputs
- clear evaluation scenarios
- safe and constrained behavior

The AI layer is therefore treated as an **engineering extension of a solid system**, not as a gimmick added on top of an unstable base.

### 1.3 What the application is useful for

- Demonstrating how to design an API that mirrors healthcare interoperability patterns in a deliberately simplified FHIR-like way
- Showcasing clean boundaries between domain, application use-cases, and infrastructure concerns
- Providing a small EHR-style viewer to validate API behavior end-to-end
- Serving as a practical base for extensions such as additional resources, export bundles, persistence adapters, and integration adapters
- Providing a future base for **grounded AI features over structured patient data**
- Demonstrating **AI Engineering** in a niche with strong professional value: health/interoperability

> Note: This is a portfolio/educational implementation. It does not claim compliance with any specific regulatory framework.

---

## 2. Objectives

### Functional objective

Enable consultation of synthetic patients and visualization of:

- patient discovery/search
- patient clinical summary
- clinical timeline resources (`Encounter`, `Condition`, `Observation`)
- biomarker time series, for example HbA1c
- export of a FHIR-like Bundle JSON
- audit visibility for patient data access and export operations

### Technical objective

Build a project that demonstrates:

- FastAPI API documented with OpenAPI, tested, and covered by CI
- SQL persistence with PostgreSQL and Alembic migrations
- layered design using Clean Architecture / Hexagonal Architecture principles
- application use-cases separated from framework and persistence details
- narrow application ports driven by real vertical slices
- JWT authentication and basic RBAC
- access auditing to clinical resources through `AuditEvent`
- strong documentation and ADR discipline
- future AI integration designed on top of:
  - structured synthetic data
  - reproducible evaluation scenarios
  - grounded responses over domain resources
  - explicit traceability
  - measurable error handling

### Career objective

Use this repository as a portfolio asset that signals strength in:

- backend/software architecture
- clean domain modeling
- application-layer design
- documentation and technical decision making
- healthcare/interoperability engineering
- and later, **Applied AI Engineering**

---

## 3. Delivery strategy

Work is organized as **phases**. Each phase may contain **sub-issues**, such as vertical slices or resource-specific tasks. Major technical decisions are documented as ADRs under `docs/adr/`.

The delivery order intentionally prioritizes:

1. a stable domain model
2. an application layer around that domain
3. an executable backend with persistence
4. reproducible synthetic datasets
5. a visible end-to-end viewer
6. and only then an AI layer built on top of stable, structured, evaluable artifacts

This is deliberate: the project should first become a good software system, and then become a good AI-enabled system.

---

## 4. Phase plan

### Phase 1 — Domain modeling

**Objective:** Define the clinical core without framework dependencies.

Scope:

- Domain entities:
  - `Patient`
  - `Observation`
  - `Condition`
  - `Encounter`
  - `AuditEvent`

- Value objects:
  - `ResourceId`
  - `Identifier`
  - `HumanName`
  - `Code`
  - `Quantity`
  - `Instant`
  - `Period`
  - `Reference`

- Basic invariants:
  - identifier consistency
  - clinical coding structure
  - quantity structure
  - timeline coherence
  - typed patient-centered references
  - timezone-aware timestamps
  - minimal audit consistency

**Definition of Done**

- Domain model documented:
  - `docs/architecture/001-value_objects_data_model.md`
  - `docs/architecture/002-entities_data_model.md`
- Unit tests for key invariants
- No FastAPI, SQLAlchemy, Pydantic, persistence, or API dependencies in the domain layer
- Phase 1 ADR/documentation completion pass finished

---

### Phase 2 — Application architecture skeleton

**Objective:** Build the application layer around the completed domain model using vertical slices and narrow application ports.

The focus is to prepare the architecture around the domain so the backend can become executable in the next phase.

Phase 2 intentionally does **not** start by designing broad generic repositories. Instead, it grows the application layer through real use-cases and lets abstractions emerge from repeated needs.

Scope:

- Define the application layer structure
- Define use-case entry points with explicit orchestration boundaries
- Model use-cases as classes exposing `execute()`
- Define application-level errors
- Define application result models only when the use-case output is not simply a domain resource or collection of domain resources
- Define narrow read-oriented ports required by each vertical slice
- Avoid premature broad CRUD-style repositories
- Test use-cases with in-memory implementations of their ports
- Keep the application layer independent from FastAPI, SQLAlchemy, Pydantic, and concrete persistence details
- Align project conventions with the actual codebase
- Clean obvious structural inconsistencies that would hinder the next phase

Initial Phase 2 / Iteration 1 use-cases:

- `SearchPatients`
- `GetPatientSummary`
- `ListObservationsByCode`
- `ExportPatientBundle`
- `ListAuditEvents`

Current application-layer principles:

- Use-cases belong to `application/use_cases/`
- Ports belong to `application/ports/`
- Application models belong to `application/models/`
- Application errors belong to `application/errors.py`
- Ports should be named around capabilities or stable read patterns, not around speculative repositories
- Returning domain entities directly is acceptable for simple list/search slices
- Dedicated application result models are preferred when a use-case composes multiple resources into a new application-level concept
- Search/list use-cases return empty collections when the query is valid but there are no matches
- Get/detail use-cases raise application-level not-found errors when the requested target resource does not exist

**Definition of Done**

- The post-domain project structure is clear and stable
- Application-layer boundaries are defined
- Initial use-cases are implemented as vertical slices
- Narrow application ports are identified and tested
- Application-layer tests are deterministic and do not depend on frameworks or persistence
- Architectural conventions are coherent with the implemented domain
- The project is ready to start the executable backend foundation without rethinking the structure again

---

### Phase 3 — Backend foundation

**Objective:** Provide an executable backend skeleton with persistence and configuration.

Scope:

- FastAPI application structure
- API configuration
- logging
- PostgreSQL persistence
- Alembic migrations
- DB session management
- concrete adapters implementing application ports
- dependency wiring from infrastructure/API adapters to application use-cases
- CI pipeline for linting and tests

**Definition of Done**

- API application boots correctly
- CI runs linting and tests
- `/health` and `/docs` are available
- Persistence infrastructure exists
- Concrete adapters implement the application ports defined in Phase 2
- Framework and persistence dependencies remain outside the domain layer and outside application use-case logic

---

### Phase 4 — Authentication, RBAC, and audit trail

**Objective:** Implement security and traceability expectations early.

Scope:

- JWT issuance and verification
- basic role model
- RBAC enforcement at the API/application boundary
- audit event capture for access to patient data and exports
- persisted audit events
- audit querying for administrative visibility

**Definition of Done**

- Protected endpoints require valid JWT
- RBAC rules are enforced and tested
- Audit trail is persisted and queryable
- Access to patient data and bundle export operations can be traced through `AuditEvent`

---

### Phase 5 — Clinical use-cases and endpoints

**Objective:** Deliver minimal clinical value through stable API endpoints.

Scope:

- Patient search endpoint
- Patient summary endpoint
- Observation listing by code endpoint
- FHIR-like Bundle export endpoint
- Audit listing endpoint

**Definition of Done**

- OpenAPI examples exist for the main endpoints
- Integration tests cover the main clinical and audit endpoints
- Application use-cases are wired through concrete adapters
- Audit events are recorded on patient access and export operations
- Endpoint contracts stay structured and predictable

**AI-readiness notes**

- Endpoint outputs should stay strongly structured and predictable
- Patient summary and export flows should be designed so they can later serve as grounding sources for AI features
- Avoid endpoint contracts that mix presentation-only text with core structured evidence in ways that would make later grounding harder
- Preserve resource identifiers, dates, codes, quantities, and references in outputs that may later support AI grounding

---

### Phase 6 — Synthetic dataset and demo scenarios

**Objective:** Make the project reproducible and easy to evaluate.

Scope:

- Seed generator for patient cohorts
- Scenario fixtures, for example:
  - diabetes HbA1c trend
  - hypertension
  - routine follow-up encounters
  - abnormal observation follow-up
- demo walkthrough
- reproducible local execution instructions

**Definition of Done**

- One command seeds demo data
- Demo scenarios are documented
- Clear “run the demo” guide exists
- Synthetic data is rich enough to demonstrate patient summary, observation filtering, timeline navigation, export, and audit behavior

**AI-readiness notes**

- Synthetic data should be richer than a minimal toy dataset
- Include enough temporal variation, repeated observations, conditions, and encounters to support later:
  - patient summary generation
  - biomarker trend interpretation
  - grounded question-answering
  - structured search/evaluation scenarios
- Prefer reproducible scenario cohorts over isolated dummy records

---

### Phase 7 — EHR-lite viewer

**Objective:** Provide a minimal UI to validate end-to-end behavior.

Scope:

- Patient search
- Patient summary and timeline
- Observation listing by code
- Basic charts for one or two biomarkers
- FHIR-like Bundle export action
- Admin audit view

**Definition of Done**

- Frontend consumes the real API
- Basic UX states exist:
  - loading
  - empty
  - error
  - success
- Viewer demonstrates the core clinical, interoperability, and traceability flows
- The UI remains small enough to be reviewable as a portfolio artifact

**AI-readiness notes**

- The UI should keep a clean separation between:
  - raw structured data
  - derived summaries
  - future AI-generated outputs
- This phase should avoid UI decisions that would make later evidence-backed AI features awkward to present
- Future AI-generated outputs should be visually traceable back to structured patient data

---

### Phase 8 — Hardening and portfolio packaging

**Objective:** Polish the project for professional presentation.

Scope:

- Architecture overview documentation
- updated directory tree documentation
- contract testing or OpenAPI snapshot checks
- quality gates in CI
- README improvements
- demo instructions
- portfolio-oriented explanation of architectural decisions

**Definition of Done**

- Repository is review-ready
- Documentation explains what the project demonstrates professionally
- Setup and test execution are reproducible
- Architectural decisions are discoverable through ADRs
- The project can be evaluated without requiring real patient data or external clinical systems

**AI-readiness notes**

- Before adding AI, the project should already be stable enough to support evaluation and reproducibility
- Observability, clean contracts, and reproducible scenarios are preferred over adding premature AI features on top of unstable foundations

---

### Phase 9 — Applied AI Engineering layer

**Objective:** Add a focused AI Engineering layer on top of the completed MVP, using structured synthetic clinical data as the source of truth.

Principles:

- No generic “medical chatbot”
- No autonomous multi-agent workflows as a first integration
- No AI feature without grounding, traceability, and evaluation
- Prefer constrained, measurable features over broad but vague assistants
- AI outputs must be backed by structured evidence from project resources

Initial candidate features:

- Grounded patient clinical summary generation
- Patient-specific Q&A over structured evidence
- Natural language to structured clinical search/filter translation

Recommended first feature:

- **Grounded patient summary generation**
  - Generate a clinically useful narrative summary from:
    - patient summary data
    - timeline items
    - observations
    - conditions
    - encounters
  - Preserve explicit grounding in the underlying structured resources

Possible second feature:

- **Patient-specific Q&A with evidence**
  - Example questions:
    - “How has HbA1c evolved?”
    - “What active conditions does this patient have?”
    - “What relevant events happened in the last year?”
  - Responses must be backed by concrete domain resources, dates, codes, and resource ids

Possible third feature:

- **Natural language search to structured filters**
  - Translate user queries such as:
    - “patients with diabetes and worsening HbA1c”
  - into safe structured filters over domain resources

**Definition of Done**

- At least one AI feature is implemented on top of the completed MVP
- The AI output is grounded in project data rather than unconstrained free generation
- The feature has a repeatable evaluation strategy
- Errors and limitations are explicitly documented
- The feature is demonstrable as **Applied AI Engineering**, not just “LLM integration”

---

## 5. Long-term extension space

Potential future extensions after the MVP and Phase 9 may include:

- richer terminology support
- broader clinical resource coverage
- more advanced audit/compliance views
- additional AI-assisted workflows
- stronger retrieval/evaluation infrastructure
- more sophisticated search and summarization features

These are intentionally deferred until the MVP and its first Applied AI Engineering layer are complete and stable.

---

## 6. Positioning summary

This project is intended to stand out as a portfolio piece at the intersection of:

- **software architecture**
- **clean backend engineering**
- **strong domain modeling**
- **healthcare/interoperability**
- **documentation and technical rigor**
- and **Applied AI Engineering**

That combination is intentional and central to the project identity.
