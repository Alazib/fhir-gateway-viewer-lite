# FHIR Mini-Gateway + EHR-lite Viewer — Roadmap

## 1. Project overview

This repository implements a small, portfolio-grade Health IT application composed of:

- a **FHIR-like API (mini gateway)** exposing a deliberately scoped subset of clinical resources, and
- an **EHR-lite viewer (mini visor)** focused on patient navigation, clinical timeline exploration, and basic biomarker trend visualization.

The goal is to demonstrate **interoperability-oriented backend engineering** with professional software practices: clean architecture, explicit technical decision records (ADRs), API documentation, testing, CI quality gates, and reproducible synthetic datasets. The application is intentionally designed to remain small, iterative, and easy to evaluate by a reviewer.

### 1.1 Why this is healthcare/biotech-specific

This project is not a generic CRUD demo. It is built around common healthcare integration concerns:

- **Resource-oriented clinical modeling** (Patient, Observation, Condition, Encounter, AuditEvent).
- **Semantic coding** (minimal terminology catalogs for observations/conditions), avoiding “free-text-only” clinical data.
- **Traceability** via **audit events** and **role-based access patterns** typically expected in regulated environments.
- **Synthetic data only**: no real patient data is used; the project includes reproducible generators/fixtures.

### 1.2 What the application is useful for

- Demonstrating how to design an API that mirrors healthcare interoperability patterns (FHIR-like).
- Showcasing clean boundaries between domain, application use-cases, and infrastructure concerns.
- Providing a small EHR-style viewer to validate API behavior end-to-end.
- Serving as a practical base for extensions (additional resources, export bundles, integration adapters).

> Note: This is a portfolio/educational implementation. It does not claim compliance with any specific regulatory framework.

---

## 2.2 Objectives

### Functional objective
- Enable **consultation** of a synthetic patient and visualization of:
  - clinical timeline (encounters, conditions, observations),
  - biomarker time series (e.g., HbA1c),
  - export of a FHIR-like **Bundle JSON**.

### Technical objective (professional signal)
- FastAPI API documented (OpenAPI), tested, and covered by CI.
- SQL persistence (PostgreSQL) and migrations.
- Layered design (Hexagonal/Clean) with ADRs for key decisions.
- JWT authentication and basic RBAC (Admin/Clinician).
- Access auditing to clinical resources (minimal AuditEvent).

---

## 3. Delivery strategy

Work is organized as **phases** (GitHub Issues). Each phase may contain **sub-issues** (e.g., vertical slices or resource-specific tasks). Major technical decisions are documented as ADRs under `docs/adr/`.

---

## 4. Phase plan

### Phase 1 — Domain modeling
**Objective:** Define the clinical core without framework dependencies.
- Domain entities: Patient, Observation, Condition, Encounter, AuditEvent
- Value objects: Code, Quantity, Period
- Basic invariants (MVP): coding consistency, unit handling, timeline coherence

**Definition of Done**
- Domain model documented (`docs/architecture/data-model.md`)
- Unit tests for key invariants
- No FastAPI/SQLAlchemy dependencies in the domain layer

---

### Phase 2 — ADR baseline and architectural skeleton
**Objective:** Lock down foundational decisions and repository conventions.
- ADRs: repo structure, Python dependency management (Pipenv), API stack, FHIR-like scope, auth strategy (JWT), RBAC model, audit strategy

**Definition of Done**
- ADRs created and accepted
- Consistent project conventions (naming, folder layout)

---

### Phase 3 — Backend foundation
**Objective:** Provide an executable API skeleton with persistence and configuration.
- FastAPI app structure, configuration, logging
- Postgres + Alembic migrations
- Repository ports/adapters and DB session management
- CI pipeline for linting + tests

**Definition of Done**
- `docker-compose` brings up API + DB
- CI runs lint + unit tests
- `/health` and `/docs` available

---

### Phase 4 — Authentication, RBAC, and audit trail
**Objective:** Implement security and traceability expectations early.
- JWT issuance and verification
- RBAC enforcement (Admin/Clinician) at the use-case boundary
- AuditEvent capture for access to patient data and exports

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

---

### Phase 6 — Synthetic dataset and demo scenarios
**Objective:** Make the project reproducible and easy to evaluate.
- Seed generator for patient cohorts
- Scenario fixtures (e.g., diabetes HbA1c trends, hypertension)
- “Run the demo” guide

**Definition of Done**
- One command seeds data
- Clear demo walkthrough in README

---

### Phase 7 — EHR-lite viewer
**Objective:** Minimal UI to validate end-to-end behavior.
- Patient search
- Patient summary and timeline
- Basic charts for 1–2 biomarkers
- Admin audit view

**Definition of Done**
- Frontend consumes real API
- Basic UX states: loading/empty/error

---

### Phase 8 — Hardening and portfolio packaging
**Objective:** Polish for professional presentation.
- Architecture overview documentation
- Contract testing or OpenAPI snapshot checks
- Quality gates in CI

**Definition of Done**
- Repo is review-ready (docs, scripts, tests, reproducibility)
