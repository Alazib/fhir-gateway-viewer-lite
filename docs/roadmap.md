# FHIR Mini-Gateway + EHR-lite Viewer + Applied AI Engineering — Roadmap

## 1. Project overview

This repository implements a small, portfolio-grade Health IT application composed of:

* a **FHIR-like API (mini gateway)** exposing a deliberately scoped subset of clinical resources, and
* an **EHR-lite viewer (mini visor)** focused on patient navigation, clinical timeline exploration, and basic biomarker trend visualization.

The project is also intentionally designed to evolve into a strong **Applied AI Engineering** portfolio case on top of structured synthetic clinical data.

The goal is to demonstrate:

* **interoperability-oriented backend engineering**
* **clean architecture and strong domain modeling**
* **professional documentation and ADR discipline**
* **testing and reproducibility**
* and later, **grounded, evaluable AI engineering** over structured health data

This application is intentionally designed to remain small, iterative, and easy to evaluate by a reviewer, while still showcasing depth in:

* architecture
* modeling
* documentation
* software quality
* and AI engineering readiness

### 1.1 Why this is healthcare/biotech-specific

This project is not a generic CRUD demo.

It is built around common healthcare integration concerns:

* **Resource-oriented clinical modeling** (`Patient`, `Observation`, `Condition`, `Encounter`, `AuditEvent`)
* **Semantic coding** through clinical codes for observations and conditions, avoiding free-text-only clinical data
* **Traceability** through audit events and role-based access patterns typically expected in regulated environments
* **Synthetic data only**: no real patient data is used; the project is intended to rely on reproducible demo data and fixtures

### 1.2 Why this is also an AI Engineering project

This project is not meant to become just a chatbot on top of data.

It is intended to become a serious **Applied AI Engineering** case by building AI features on top of:

* structured clinical resources
* reproducible synthetic datasets
* explicit grounding
* auditable outputs
* clear evaluation scenarios
* safe and constrained behavior

The AI layer is therefore treated as an engineering extension of a solid system, not as a feature added on top of an unstable base.

### 1.3 What the application is useful for

* Demonstrating how to design an API that mirrors healthcare interoperability patterns in a deliberately simplified FHIR-like way
* Showcasing clean boundaries between domain, application use-cases, and infrastructure concerns
* Providing a small EHR-style viewer to validate API behavior end-to-end
* Serving as a practical base for additional resources, export bundles, persistence adapters, and integration adapters
* Providing a future base for grounded AI features over structured patient data
* Demonstrating AI Engineering in a niche with strong professional value: health/interoperability

> Note: This is a portfolio/educational implementation. It does not claim compliance with any specific regulatory framework.

---

## 2. Objectives

### Functional objective

Enable consultation of synthetic patients and visualization of:

* patient discovery/search
* patient clinical summary
* clinical timeline resources (`Encounter`, `Condition`, `Observation`)
* biomarker time series, for example HbA1c
* export of a FHIR-like Bundle JSON
* audit visibility for patient data access and export operations

### Technical objective

Build a project that demonstrates:

* FastAPI API documented with OpenAPI, tested, and covered by CI
* SQL persistence with PostgreSQL and Alembic migrations
* layered design using Clean Architecture / Hexagonal Architecture principles
* application use-cases separated from framework and persistence details
* narrow application ports driven by real vertical slices
* JWT authentication and basic RBAC
* access auditing to clinical resources through `AuditEvent`
* strong documentation and ADR discipline
* future AI integration designed on top of:
  * structured synthetic data
  * reproducible evaluation scenarios
  * grounded responses over domain resources
  * explicit traceability
  * measurable error handling

### Career objective

Use this repository as a portfolio asset that signals strength in:

* backend/software architecture
* clean domain modeling
* application-layer design
* documentation and technical decision making
* healthcare/interoperability engineering
* and later, **Applied AI Engineering**

---

## 3. Delivery strategy and current status

Work is organized as phases. Each phase may contain sub-issues, such as vertical slices or resource-specific tasks. Major technical decisions are documented as ADRs under `docs/adr/`.

The delivery order intentionally prioritizes:

1. a stable domain model
2. an application layer around that domain
3. an executable backend with persistence
4. a security and audit foundation
5. stable clinical HTTP endpoints
6. reproducible synthetic datasets
7. a visible end-to-end viewer
8. hardening and portfolio packaging
9. an AI layer built on top of stable, structured, evaluable artifacts

This is deliberate: the project should first become a good software system, and then become a good AI-enabled system.

Current project work:

```text
Phase 4 — Authentication, RBAC, audit trail, error contract, and security documentation
```

Current Phase 4 status:

```text
Completed:
A. MVP security model ADR
B. API error response envelope and initial error mappings
C. Initial security README and API README security reference
D. JWT settings and token verification foundation
E. CurrentPrincipal and HTTP Bearer authentication dependency

Next:
F. RBAC permission model and authorization helpers
```

Phase 3 is complete.

---

## 4. Phase plan

### Phase 1 — Domain modeling

**Status:** Completed

**Objective:** Define the clinical core without framework dependencies.

Scope:

* Domain entities:
  * `Patient`
  * `Observation`
  * `Condition`
  * `Encounter`
  * `AuditEvent`
* Value objects:
  * `ResourceId`
  * `Identifier`
  * `HumanName`
  * `Code`
  * `Quantity`
  * `Instant`
  * `Period`
  * `Reference`
* Basic invariants:
  * identifier consistency
  * clinical coding structure
  * quantity structure
  * timeline coherence
  * typed patient-centered references
  * timezone-aware timestamps
  * minimal audit consistency

**Definition of Done**

* Domain model documented:
  * `docs/architecture/001-value_objects_data_model.md`
  * `docs/architecture/002-entities_data_model.md`
* Unit tests for key invariants
* No FastAPI, SQLAlchemy, Pydantic, persistence, or API dependencies in the domain layer
* Phase 1 ADR/documentation completion pass finished

---

### Phase 2 — Application architecture skeleton

**Status:** Completed

**Objective:** Build the application layer around the completed domain model using vertical slices and narrow application ports.

Phase 2 intentionally does not start by designing broad generic repositories. It grows the application layer through real use-cases and lets abstractions emerge from repeated needs.

Scope:

* Define the application layer structure
* Define use-case entry points with explicit orchestration boundaries
* Model use-cases as classes exposing `execute()`
* Define application-level errors
* Define application result models only when a use-case output is not simply a domain resource or collection
* Define narrow read-oriented ports required by each vertical slice
* Avoid premature broad CRUD-style repositories
* Test use-cases with in-memory implementations of their ports
* Keep application independent from FastAPI, SQLAlchemy, Pydantic, and concrete persistence details

Initial Phase 2 / Iteration 1 use-cases:

* `SearchPatients`
* `GetPatientSummary`
* `ListObservationsByCode`
* `ExportPatientBundle`
* `ListAuditEvents`

Application-layer principles:

* Use-cases belong to `application/use_cases/`
* Ports belong to `application/ports/`
* Application models belong to `application/models/`
* Application errors belong to `application/errors.py`
* Ports are named around capabilities or stable read patterns
* Returning domain entities directly is acceptable for simple list/search slices
* Dedicated result models are preferred when a use-case composes multiple resources
* Search/list use-cases return empty collections for valid queries without matches
* Get/detail use-cases raise application-level not-found errors when the target does not exist

**Definition of Done**

* Application-layer boundaries are defined
* Initial use-cases are implemented as vertical slices
* Narrow application ports are identified and tested
* Application tests are deterministic and framework-independent
* Architectural conventions are coherent with the domain
* The project is ready for executable backend work

---

### Phase 3 — Backend foundation

**Status:** Completed

**Objective:** Provide an executable backend skeleton with persistence and configuration.

Scope:

* FastAPI application structure
* API configuration and logging
* PostgreSQL persistence foundation
* SQLAlchemy base, ORM models, engine, and session factory
* Alembic migrations
* request-scoped database session management
* timestamp strategy
* logical deletion strategy
* AuditEvent persistence strategy
* ORM-to-domain mappers
* concrete SQLAlchemy read adapters
* dependency wiring from infrastructure adapters to application use-cases
* CI pipeline for linting and tests

**Definition of Done**

* API application boots correctly
* CI runs linting and tests
* `/health` and `/docs` are available
* Persistence infrastructure exists
* SQLAlchemy ORM models exist for MVP resources
* Alembic migrations exist for the MVP schema
* ORM-to-domain mappers exist
* Concrete adapters implement Phase 2 ports
* HTTP dependencies compose sessions, adapters, and use-cases
* Framework and persistence dependencies remain outside domain and application

---

### Phase 4 — Authentication, RBAC, audit trail, error contract, and security documentation

**Status:** In progress

**Objective:** Establish the professional MVP security, authorization, audit-write, and API error foundations required before exposing persistence-backed clinical endpoints.

Scope:

* MVP security model ADR
* standard API error response envelope
* centralized mapping of application, domain, authentication, authorization, and internal errors
* dedicated security documentation
* JWT runtime settings
* local/MVP HS256 token verification
* `VerifiedJwtClaims`
* request-scoped `CurrentPrincipal`
* reusable Bearer authentication dependency
* explicit roles and permissions
* independently testable RBAC policy
* `403 Forbidden` authorization behavior
* trusted audit actor derivation
* audit write-side port and use-case foundation
* reusable security and audit dependencies for later protected endpoints
* architecture boundary tests
* final Phase 4 documentation and quality-gate update

Completed sub-issues:

```text
A. Define MVP security model ADR
B. Define API error response envelope and initial security error mapping
C. Create initial security README and API README security reference
D. Add security settings and token verification foundation
E. Add CurrentPrincipal and HTTP authentication dependency
```

Next sub-issue:

```text
F. Add RBAC permission model and authorization helpers
```

Remaining sequence:

```text
F. RBAC permission model and authorization helpers
G. Audit write-side port and use-case foundation
H. Security and audit dependency wiring for future protected endpoints
I. Final API, security documentation, and quality-gate update
```

Important boundaries:

* `/health` remains public.
* Authentication is not applied globally.
* No production clinical or audit router is introduced solely to test security.
* Token verification belongs to infrastructure.
* `CurrentPrincipal` and pure authorization policy belong outside FastAPI.
* HTTP dependencies and HTTP error translation belong to the interface layer.
* The audit actor comes from trusted runtime context, never from arbitrary request payloads.
* Local/demo token issuing is deferred to Phase 5.
* The AuditEvent persistence schema was delivered in Phase 3; Phase 4 adds the write-side and trusted-actor foundations.

**Definition of Done**

* MVP security ADR is accepted
* API error envelope exists and is documented
* Authentication uses consistent `401 Unauthorized` behavior
* Authorization uses consistent `403 Forbidden` behavior
* JWT settings and verification are centralized
* `CurrentPrincipal` exists and is request-scoped
* Role/permission model exists
* Authorization helpers are independently testable
* Audit actor derivation uses trusted security context
* Audit write-side application foundation exists
* Reusable security/audit dependencies are available for Phase 5
* Architecture boundaries are protected by tests
* Documentation reflects the actual implementation
* Ruff and pytest remain green

---

### Phase 5 — Clinical use-cases and endpoints

**Status:** Planned

**Objective:** Deliver minimal clinical value through stable, protected API endpoints.

Phase 5 exposes the first protected clinical and audit HTTP endpoints using the security foundation introduced in Phase 4.

Scope:

* local/demo token issuing endpoint for MVP and UI simulation
* patient search endpoint
* patient summary endpoint
* observation listing by code endpoint
* FHIR-like Bundle export endpoint
* audit listing endpoint

The demo token endpoint is intended only for local, test, development, or demo usage. It allows the UI and integration tests to obtain a Bearer JWT without implementing database-backed users, password login, external OAuth/OIDC, or a full authentication provider.

Example intended flow:

```text
UI
  -> POST /auth/demo-token
  -> receives demo JWT
  -> calls protected clinical endpoints with Authorization: Bearer <token>
```

This endpoint must not be treated as production authentication.

**Definition of Done**

* Demo token endpoint exists for non-production usage
* Demo token endpoint is disabled or rejected in production
* Demo token endpoint can issue tokens for supported MVP roles
* Protected endpoints require Bearer authentication and permissions
* Patient search endpoint exists
* Patient summary endpoint exists
* Observation listing by code endpoint exists
* FHIR-like Bundle export endpoint exists
* Audit listing endpoint exists
* OpenAPI examples exist for main endpoints
* Integration tests cover main clinical and audit endpoints
* Application use-cases are wired through concrete adapters
* Selected patient access and export operations record audit events
* Endpoint contracts remain structured and predictable

Security notes:

* The demo token endpoint is an MVP convenience, not a production identity system.
* It must not introduce registration, password login, refresh tokens, sessions, or database-backed users.
* Issued tokens must follow the Phase 4 claim contract.
* Clinical and audit endpoints must use Phase 4 authentication and authorization.
* Audit actors must be derived from `CurrentPrincipal`, not request bodies.

AI-readiness notes:

* Endpoint outputs remain strongly structured and predictable.
* Patient summary and export flows can later serve as grounding sources.
* Presentation-only text must not replace structured clinical evidence.
* Resource identifiers, dates, codes, quantities, and references are preserved.

---

### Phase 6 — Synthetic dataset and demo scenarios

**Status:** Planned

**Objective:** Make the project reproducible and easy to evaluate.

Scope:

* Seed generator for patient cohorts
* Scenario fixtures, for example:
  * diabetes HbA1c trend
  * hypertension
  * routine follow-up encounters
  * abnormal observation follow-up
* demo walkthrough
* reproducible local execution instructions

**Definition of Done**

* One command seeds demo data
* Demo scenarios are documented
* Clear run-the-demo guide exists
* Synthetic data demonstrates summary, observation filtering, timeline, export, and audit behavior

AI-readiness notes:

* Synthetic data is richer than a minimal toy dataset.
* It includes temporal variation, repeated observations, conditions, and encounters.
* Scenario cohorts are reproducible and suitable for later evaluation.

---

### Phase 7 — EHR-lite viewer

**Status:** Planned

**Objective:** Provide a minimal UI to validate end-to-end behavior.

Scope:

* Patient search
* Patient summary and timeline
* Observation listing by code
* Basic charts for one or two biomarkers
* FHIR-like Bundle export action
* Admin audit view

**Definition of Done**

* Frontend consumes the real API
* Loading, empty, error, and success states exist
* Viewer demonstrates core clinical, interoperability, and traceability flows
* UI remains small and reviewable as a portfolio artifact

AI-readiness notes:

* Raw structured data, derived summaries, and future AI output remain visually distinct.
* Future AI output is traceable to structured patient evidence.

---

### Phase 8 — Hardening and portfolio packaging

**Status:** Planned

**Objective:** Polish the project for professional presentation.

Scope:

* architecture overview documentation
* updated directory tree documentation
* contract testing or OpenAPI snapshot checks
* quality gates in CI
* README improvements
* demo instructions
* portfolio-oriented explanation of architectural decisions

**Definition of Done**

* Repository is review-ready
* Documentation explains professional value
* Setup and tests are reproducible
* ADRs make decisions discoverable
* Evaluation requires no real patient data or external clinical systems

AI-readiness notes:

* The project is stable enough to support evaluation and reproducibility before AI is added.
* Observability, clean contracts, and reproducible scenarios take priority over premature AI features.

---

### Phase 9 — Applied AI Engineering layer

**Status:** Planned

**Objective:** Add a focused AI Engineering layer on top of the completed MVP, using structured synthetic clinical data as the source of truth.

Principles:

* No generic medical chatbot
* No autonomous multi-agent workflow as the first integration
* No AI feature without grounding, traceability, and evaluation
* Prefer constrained, measurable features
* AI output must be backed by structured project evidence

Initial candidate features:

* grounded patient clinical summary generation
* patient-specific Q&A over structured evidence
* natural-language-to-structured-search translation

Recommended first feature:

**Grounded patient summary generation**

Generate a clinically useful narrative summary from patient summary data, timeline items, observations, conditions, and encounters while preserving explicit grounding in the underlying resources.

Possible second feature:

**Patient-specific Q&A with evidence**

Example questions:

* How has HbA1c evolved?
* What active conditions does this patient have?
* What relevant events happened in the last year?

Responses must be backed by concrete resources, dates, codes, and resource IDs.

Possible third feature:

**Natural language search to structured filters**

Translate queries such as:

```text
patients with diabetes and worsening HbA1c
```

into safe structured filters over domain resources.

**Definition of Done**

* At least one AI feature exists on top of the completed MVP
* Output is grounded in project data
* The feature has a repeatable evaluation strategy
* Errors and limitations are documented
* The result demonstrates Applied AI Engineering, not only LLM integration

---

## 5. Long-term extension space

Potential future extensions after the MVP and Phase 9 may include:

* richer terminology support
* broader clinical resource coverage
* more advanced audit/compliance views
* additional AI-assisted workflows
* stronger retrieval/evaluation infrastructure
* more sophisticated search and summarization features

These are intentionally deferred until the MVP and its first Applied AI Engineering layer are complete and stable.

---

## 6. Positioning summary

This project is intended to stand out as a portfolio piece at the intersection of:

* **software architecture**
* **clean backend engineering**
* **strong domain modeling**
* **healthcare/interoperability**
* **documentation and technical rigor**
* and **Applied AI Engineering**

That combination is intentional and central to the project identity.
