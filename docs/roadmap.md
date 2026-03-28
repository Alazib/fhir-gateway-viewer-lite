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

This project is not a generic CRUD demo. It is built around common healthcare integration concerns:

- **Resource-oriented clinical modeling** (`Patient`, `Observation`, `Condition`, `Encounter`, `AuditEvent`)
- **Semantic coding** (minimal terminology catalogs for observations/conditions), avoiding “free-text-only” clinical data
- **Traceability** via **audit events** and **role-based access patterns** typically expected in regulated environments
- **Synthetic data only**: no real patient data is used; the project includes reproducible generators/fixtures

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

- Demonstrating how to design an API that mirrors healthcare interoperability patterns (FHIR-like)
- Showcasing clean boundaries between domain, application use-cases, and infrastructure concerns
- Providing a small EHR-style viewer to validate API behavior end-to-end
- Serving as a practical base for extensions (additional resources, export bundles, integration adapters)
- Providing a future base for **grounded AI features over structured patient data**
- Demonstrating **AI Engineering** in a niche with strong professional value: health/interoperability

> Note: This is a portfolio/educational implementation. It does not claim compliance with any specific regulatory framework.

---

## 2. Objectives

### Functional objective
Enable **consultation** of synthetic patients and visualization of:

- clinical timeline (`Encounter`, `Condition`, `Observation`)
- biomarker time series (e.g., HbA1c)
- export of a FHIR-like **Bundle JSON**

### Technical objective (professional signal)
Build a project that demonstrates:

- FastAPI API documented (OpenAPI), tested, and covered by CI
- SQL persistence (PostgreSQL) and migrations
- Layered design (Hexagonal/Clean) with ADRs for key decisions
- JWT authentication and basic RBAC (Admin/Clinician)
- Access auditing to clinical resources (`AuditEvent`)
- Strong documentation and domain modeling
- Future AI integration designed on top of:
  - structured synthetic data
  - reproducible evaluation scenarios
  - grounded responses over domain resources
  - explicit traceability
  - measurable error handling

### Career objective
Use this repository as a portfolio asset that signals strength in:

- backend/software architecture
- clean modeling and domain design
- documentation and technical decision making
- healthcare/interoperability engineering
- and later, **Applied AI Engineering**

---

## 3. Delivery strategy

Work is organized as **phases** (GitHub Issues). Each phase may contain **sub-issues** (e.g., vertical slices or resource-specific tasks). Major technical decisions are documented as ADRs under `docs/adr/`.

The delivery order intentionally prioritizes:

1. a stable domain
2. an application skeleton around that domain
3. an executable backend with persistence
4. reproducible synthetic datasets
5. a visible end-to-end viewer
6. and only then an AI layer built on top of stable, structured, evaluable artifacts

This is deliberate: the project should first become a good software system, and then become a good AI-enabled system.

---

## 4. Phase plan

### Phase 1 — Domain modeling
**Objective:** Define the clinical core without framework dependencies.

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
- Basic invariants (MVP):
  - coding consistency
  - unit handling
  - timeline coherence
  - typed patient-centered references
  - timezone-aware timestamps
  - minimal audit consistency

**Definition of Done**
- Domain model documented:
  - `docs/architecture/001-value_objects_data_model.md`
  - `docs/architecture/002-entities_data_model.md`
- Unit tests for key invariants
- No FastAPI/SQLAlchemy dependencies in the domain layer
- Phase 1 ADR/documentation completion pass finished

---

### Phase 2 — Application architecture skeleton
**Objective:** Build the application-layer and repository skeleton around the completed domain model.


The focus is to prepare the **architecture around the domain** so the backend can become executable in the next phase.

- Define the application layer structure
- Define use-case entry points / service layer boundaries
- Define repository interfaces / ports around the domain
- Define infrastructure package layout and wiring strategy
- Align project conventions with the actual codebase
- Clean obvious structural inconsistencies that would hinder the next phase

**Definition of Done**
- The post-domain project structure is clear and stable
- Application-layer boundaries are defined
- Repository/service interfaces are identified
- Architectural conventions are coherent with the implemented domain
- The project is ready to start the executable backend foundation without rethinking the structure again

---

### Phase 3 — Backend foundation
**Objective:** Provide an executable backend skeleton with persistence and configuration.

- FastAPI app structure
- configuration
- logging
- PostgreSQL + Alembic migrations
- DB session management
- concrete repository adapters
- CI pipeline for linting + tests

**Definition of Done**
- API application boots correctly
- CI runs lint + unit tests
- `/health` and `/docs` available
- Persistence infrastructure exists and is wired to the application structure defined in Phase 2

---

### Phase 4 — Authentication, RBAC, and audit trail
**Objective:** Implement security and traceability expectations early.

- JWT issuance and verification
- RBAC enforcement (Admin/Clinician) at the use-case boundary
- `AuditEvent` capture for access to patient data and exports

**Definition of Done**
- Protected endpoints require valid JWT
- RBAC rules enforced and tested
- Audit trail persisted and queryable (admin)

---

### Phase 5 — Clinical use-cases and endpoints
**Objective:** Deliver minimal clinical value via stable endpoints.

- Search patients
- Patient summary (timeline aggregation)
- Observation listing by code
- Export Bundle (FHIR-like JSON)

**Definition of Done**
- OpenAPI examples in `docs/api/examples/`
- Integration tests for main endpoints
- Audit events recorded on access/export

**AI-readiness notes**
- Endpoint outputs should stay strongly structured and predictable
- Patient summary and export flows should be designed so they can later serve as grounding sources for AI features
- Avoid endpoint contracts that mix presentation-only text with core structured evidence in ways that would make later grounding harder

---

### Phase 6 — Synthetic dataset and demo scenarios
**Objective:** Make the project reproducible and easy to evaluate.

- Seed generator for patient cohorts
- Scenario fixtures (e.g., diabetes HbA1c trends, hypertension)
- “Run the demo” guide

**Definition of Done**
- One command seeds data
- Clear demo walkthrough in README

**AI-readiness notes**
- Synthetic data should be richer than a minimal toy dataset
- Include enough temporal variation, repeated observations, conditions, and encounters to support later:
  - patient summary generation
  - biomarker trend interpretation
  - grounded question-answering
  - search/evaluation scenarios
- Prefer reproducible scenario cohorts over isolated dummy records

---

### Phase 7 — EHR-lite viewer
**Objective:** Minimal UI to validate end-to-end behavior.

- Patient search
- Patient summary and timeline
- Basic charts for 1–2 biomarkers
- Admin audit view

**Definition of Done**
- Frontend consumes real API
- Basic UX states: loading / empty / error

**AI-readiness notes**
- The UI should keep a clean separation between:
  - raw structured data
  - derived summaries
  - future AI-generated outputs
- This phase should avoid UI decisions that would make later evidence-backed AI features awkward to present

---

### Phase 8 — Hardening and portfolio packaging
**Objective:** Polish for professional presentation.

- Architecture overview documentation
- Contract testing or OpenAPI snapshot checks
- Quality gates in CI

**Definition of Done**
- Repo is review-ready (docs, scripts, tests, reproducibility)

**AI-readiness notes**
- Before adding AI, the project should already be stable enough to support evaluation and reproducibility
- Observability, clean contracts, and reproducible scenarios are preferred over adding premature AI features on top of unstable foundations

---

### Phase 9 — Applied AI Engineering layer
**Objective:** Add a focused AI Engineering layer on top of the completed MVP, using structured synthetic clinical data as the source of truth.

**Principles**
- No generic “medical chatbot”
- No autonomous multi-agent workflows as a first integration
- No AI feature without grounding, traceability, and evaluation
- Prefer constrained, measurable features over broad but vague assistants

**Initial candidate features**
- Grounded patient clinical summary generation
- Patient-specific Q&A over structured evidence
- Natural language to structured clinical search/filter translation

**Recommended first feature**
- **Grounded patient summary generation**
  - Generate a clinically useful narrative summary from:
    - patient summary data
    - timeline items
    - observations
    - conditions
    - encounters
  - with explicit grounding in the underlying structured resources

**Possible second feature**
- **Patient-specific Q&A with evidence**
  - Example questions:
    - “How has HbA1c evolved?”
    - “What active conditions does this patient have?”
    - “What relevant events happened in the last year?”
  - Responses must be backed by concrete domain resources and dates

**Possible third feature**
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
