# ADR 0011: HTTP API structure and runtime composition

## Status

Accepted

## Context

Phase 3 introduces the executable backend foundation.

The project already has:

- a framework-agnostic domain layer
- an application layer with use-cases and narrow ports
- an initial FastAPI HTTP interface
- a health endpoint
- infrastructure settings and logging baseline

As the API grows, it will expose application use-cases such as:

- `SearchPatients`
- `GetPatientSummary`
- `ListObservationsByCode`
- `ExportPatientBundle`
- `ListAuditEvents`

The project needs an HTTP structure that can grow without putting route definitions, runtime configuration, logging, persistence, and business logic into a single file.

## Decision

Structure the HTTP API as a thin interface layer.

The HTTP interface will use:

- a FastAPI application factory
- router modules grouped by API area
- infrastructure settings for runtime configuration
- infrastructure logging setup during application creation

Current structure:

    interfaces/http/
    ├── app.py
    ├── main.py
    └── routers/
        └── health.py

Responsibilities:

- `main.py` exposes the ASGI `app` object for Uvicorn.
- `app.py` creates and configures the FastAPI application.
- router modules define HTTP endpoints.
- infrastructure settings provide runtime configuration.
- infrastructure logging configures runtime logging.

Routers must remain thin.

Routers may:

- parse HTTP input
- build value objects
- call application use-cases
- map application results to HTTP responses

Routers must not:

- contain domain rules
- orchestrate clinical workflows directly
- contain SQLAlchemy queries
- construct patient summaries or bundles manually
- bypass application use-cases

## Rationale

The API is an adapter into the application layer, not the center of the system.

The domain layer must remain independent from:

- FastAPI
- HTTP
- Pydantic API schemas
- SQLAlchemy
- runtime configuration

The application layer must remain independent from:

- FastAPI
- HTTP request/response objects
- SQLAlchemy
- persistence details
- runtime settings

This keeps the core use-cases reusable from other possible interfaces, such as CLI commands, background workers, or message consumers.

Example future flow:

    HTTP request:
    GET /patients/pat-001/summary

    HTTP router:
    - receives `patient_id` as a string
    - builds `ResourceId("pat-001")`
    - calls `GetPatientSummaryUseCase.execute(...)`
    - maps the result to an HTTP response

    Application use-case:
    - retrieves the patient
    - retrieves related clinical resources
    - returns a `PatientSummary`

    Infrastructure adapters:
    - implement application ports using concrete technologies such as SQLAlchemy

This separation prevents FastAPI routes from becoming the place where business logic and persistence logic are mixed.

## Alternatives considered

### 1. Put all endpoints and setup in `main.py`

Rejected.

This is acceptable for very small demos, but it does not scale well.

As the API grows, `main.py` would accumulate app creation, route definitions, configuration, logging, exception handlers, dependency wiring, and persistence concerns.

### 2. Let routers directly access the database

Rejected.

This would couple HTTP endpoints to persistence and bypass the application use-cases.

It would make the system harder to test, harder to reuse, and less aligned with the existing domain/application architecture.

### 3. Put settings in the application or domain layers

Rejected.

Settings are runtime infrastructure concerns.

The domain and application layers should not depend on environment variables, FastAPI runtime settings, or logging configuration.

### 4. Introduce a full production-grade API platform immediately

Rejected.

Features such as authentication, RBAC, structured logging, request correlation IDs, advanced exception envelopes, OpenTelemetry, and deployment-specific settings are valuable but premature for the current phase.

They should be introduced when the project has a real consumer for them.

## Consequences

### Positive

- HTTP structure can grow without turning `main.py` into a mixed-responsibility file.
- Domain and application layers remain framework-independent.
- Routers stay focused on HTTP adaptation.
- Runtime configuration is centralized.
- Logging is configured consistently at application startup.
- Future persistence adapters can implement application ports without changing use-cases.
- The architecture is easier to explain in a portfolio or technical interview.

### Negative / Trade-offs

- There are more files than in a minimal FastAPI tutorial.
- The structure may feel slightly heavier at the beginning.
- Developers must understand the difference between interface, application, domain, and infrastructure layers.

The additional structure is accepted because the project is intended to demonstrate professional architecture, not only minimal functionality.

## Notes

This ADR does not define final clinical endpoint contracts.

It also does not define:

- final API error response envelope
- authentication strategy
- RBAC strategy
- persistence model strategy
- deployment model
- observability strategy

Those decisions will be documented separately when they become necessary.
