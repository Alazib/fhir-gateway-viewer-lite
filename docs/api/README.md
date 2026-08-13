# FHIR Mini-Gateway API Documentation

## Table of contents

* [1. Status](#1-status)
* [2. Purpose](#2-purpose)
* [3. Current HTTP structure](#3-current-http-structure)
* [4. Runtime configuration](#4-runtime-configuration)
* [5. Logging](#5-logging)
* [6. Persistence status](#6-persistence-status)
* [7. HTTP dependency wiring](#7-http-dependency-wiring)
* [8. Security documentation](#8-security-documentation)
* [9. Local development](#9-local-development)
* [10. Running the API locally](#10-running-the-api-locally)
* [11. Interactive documentation](#11-interactive-documentation)
* [12. Endpoint: Health check](#12-endpoint-health-check)
* [13. Error handling](#13-error-handling)
* [14. Testing and quality gate](#14-testing-and-quality-gate)
* [15. Continuous integration](#15-continuous-integration)
* [16. Current limitations](#16-current-limitations)
* [17. Planned endpoints](#17-planned-endpoints)
* [18. Logical deletion API behavior](#18-logical-deletion-api-behavior)
* [19. Audit API behavior](#19-audit-api-behavior)
* [20. API design principles](#20-api-design-principles)
* [21. Security status](#21-security-status)
* [22. Related documentation](#22-related-documentation)

---

## 1. Status

Current API status:

```text
Phase 4 / Security foundation in progress
```

Completed Phase 4 sub-issues:

```text
A. MVP security model ADR
B. API error response envelope and initial error mappings
C. Initial security README and API README security reference
D. JWT settings and token verification foundation
E. CurrentPrincipal and HTTP Bearer authentication dependency
```

Next Phase 4 sub-issue:

```text
F. RBAC permission model and authorization helpers
```

The API currently exposes one production HTTP endpoint:

```text
GET /health
```

The backend includes:

* clean FastAPI application structure
* centralized runtime configuration
* logging baseline
* SQLAlchemy/Alembic persistence foundation
* Patient, Observation, Condition, Encounter, and AuditEvent persistence schemas
* logical deletion metadata for top-level clinical resources
* ORM/domain mappers
* SQLAlchemy read adapters for current application ports
* request-scoped SQLAlchemy sessions
* HTTP dependency wiring for current read-side use-cases
* standard API error response envelope
* centralized handlers for project-owned HTTP errors
* JWT runtime settings
* infrastructure-level JWT verifier
* typed `VerifiedJwtClaims`
* application-level `CurrentPrincipal`
* reusable HTTP Bearer current-principal dependency
* architecture tests protecting SQLAlchemy, FastAPI, and PyJWT boundaries
* Ruff and pytest quality-gate commands
* GitHub Actions API CI workflow
* dedicated security documentation
* UML documentation for dependency resolution and error handling

Clinical HTTP endpoints are not implemented yet.

Audit HTTP endpoints are not implemented yet.

RBAC authorization, permission helpers, and `403 Forbidden` are not implemented yet.

No production clinical or audit endpoint currently consumes the authentication dependency.

For persistence details, see:

```text
docs/persistence/README.md
```

For security details, see:

```text
docs/security/README.md
```

---

## 2. Purpose

The FHIR Mini-Gateway API is the HTTP backend interface for the `FHIR Gateway Viewer Lite` project.

Its long-term goal is to expose a deliberately scoped FHIR-like API over synthetic clinical data, focused on:

* clean backend architecture
* healthcare interoperability concepts
* structured clinical resources
* traceability
* future EHR-lite viewer integration
* future grounded Applied AI Engineering features

This project must only use synthetic/demo data.

Do not use real patient data.

---

## 3. Current HTTP structure

### 3.1. Package structure

Current structure:

```text
apps/api/src/fhir_gateway/interfaces/http/
├── __init__.py
├── app.py
├── error_handlers.py
├── errors.py
├── main.py
├── dependencies/
│   ├── __init__.py
│   ├── adapters.py
│   ├── database.py
│   ├── security.py
│   └── use_cases.py
├── routers/
│   ├── __init__.py
│   └── health.py
└── schemas/
    ├── __init__.py
    └── errors.py
```

### 3.2. Responsibilities

* `app.py`: creates and configures the FastAPI application, application-scoped session factory, and JWT verifier.
* `main.py`: exposes the ASGI `app` object used by Uvicorn.
* `error_handlers.py`: registers exception handlers and builds the standard API error envelope.
* `errors.py`: defines HTTP/interface-layer errors such as `AuthenticationError`.
* `dependencies/database.py`: exposes request-scoped SQLAlchemy session access.
* `dependencies/adapters.py`: builds SQLAlchemy read adapters from the current session.
* `dependencies/use_cases.py`: builds application use-cases from concrete adapters.
* `dependencies/security.py`: extracts Bearer credentials, verifies the JWT, and builds `CurrentPrincipal`.
* `routers/health.py`: defines the public `/health` endpoint.
* `schemas/errors.py`: defines `ApiError` and `ApiErrorResponse`.

### 3.3. Boundary rules

The HTTP layer may depend on FastAPI.

The HTTP dependency layer may compose:

* application use-cases
* infrastructure adapters
* SQLAlchemy session management
* JWT security infrastructure

The domain and application layers must not depend on:

* FastAPI
* SQLAlchemy
* PyJWT

Application and domain errors remain framework-independent.

HTTP error mapping belongs to the HTTP/interface layer.

JWT verification belongs to infrastructure/security.

`CurrentPrincipal` belongs to application/security and remains independent from FastAPI and PyJWT.

---

## 4. Runtime configuration

### 4.1. Settings location

```text
apps/api/src/fhir_gateway/infrastructure/config/settings.py
```

### 4.2. Current settings

| Setting | Environment variable | Default |
|---|---|---|
| `app_name` | `FHIR_GATEWAY_APP_NAME` | `FHIR Mini-Gateway API` |
| `app_version` | `FHIR_GATEWAY_APP_VERSION` | `0.1.0` |
| `environment` | `FHIR_GATEWAY_ENVIRONMENT` | `local` |
| `log_level` | `FHIR_GATEWAY_LOG_LEVEL` | `INFO` |
| `database_url` | `FHIR_GATEWAY_DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/fhir_gateway` |
| `auth_jwt_secret` | `FHIR_GATEWAY_AUTH_JWT_SECRET` | `None` |
| `auth_jwt_issuer` | `FHIR_GATEWAY_AUTH_JWT_ISSUER` | `fhir-gateway-local` |
| `auth_jwt_audience` | `FHIR_GATEWAY_AUTH_JWT_AUDIENCE` | `fhir-gateway-api` |
| `auth_jwt_algorithm` | `FHIR_GATEWAY_AUTH_JWT_ALGORITHM` | `HS256` |

### 4.3. Allowed environment values

```text
local
test
development
production
```

### 4.4. Allowed log levels

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

### 4.5. Example PowerShell overrides

```powershell
$env:FHIR_GATEWAY_LOG_LEVEL = "DEBUG"
$env:FHIR_GATEWAY_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/fhir_gateway"

$env:FHIR_GATEWAY_AUTH_JWT_SECRET = "local-development-secret-at-least-32-bytes"
$env:FHIR_GATEWAY_AUTH_JWT_ISSUER = "fhir-gateway-local"
$env:FHIR_GATEWAY_AUTH_JWT_AUDIENCE = "fhir-gateway-api"
$env:FHIR_GATEWAY_AUTH_JWT_ALGORITHM = "HS256"
```

Secrets shown in examples are local/demo values only.

Do not commit a real secret.

### 4.6. Configuration principle

Settings are loaded through `pydantic-settings`.

Runtime configuration is centralized so logging, persistence, and JWT infrastructure do not implement separate environment-variable mechanisms.

---

## 5. Logging

### 5.1. Location

```text
apps/api/src/fhir_gateway/infrastructure/logging.py
```

### 5.2. Current format

```text
%(asctime)s %(levelname)s [%(name)s] %(message)s
```

### 5.3. Behavior

Logging is configured during FastAPI application creation.

Unexpected HTTP errors are logged internally before returning a generic `500 Internal Server Error`.

JWT verifier configuration errors are also logged internally.

Sensitive data must not be exposed to clients or written unnecessarily to logs:

* raw JWTs
* signing secrets
* detailed token-verification internals
* stack traces in HTTP responses

---

## 6. Persistence status

### 6.1. Current foundation

Implemented:

* SQLAlchemy ORM
* Alembic
* Psycopg 3
* centralized database URL
* database engine and session factory
* Patient and Patient identifier schemas
* Observation and Condition catalog schemas
* Observation, Condition, and Encounter schemas
* AuditEvent schema
* logical deletion metadata
* ORM/domain mappers
* SQLAlchemy read adapters
* request-scoped session dependency
* use-case dependency wiring

No production clinical or audit endpoint consumes this wiring yet.

### 6.2. Logical deletion

Top-level clinical tables with `deleted_at`:

```text
patients
observations
conditions
encounters
```

The API does not expose `deleted_at`.

### 6.3. Audit table

```text
audit_events
```

Audit events are append-oriented and do not use ordinary clinical logical deletion.

### 6.4. Migration chain

```text
<base>
    ↓
f97f9d019499_create_patient_tables
    ↓
ab48a83daad7_add_clinical_resource_tables
    ↓
d4e8f2a1c9b7_add_logical_deletion_columns_to_clinical_resources
    ↓
a6f3c9d2e1b8_add_audit_event_table
```

### 6.5. Persistence documentation

```text
docs/persistence/README.md
```

Related ADRs:

```text
docs/adr/0012-Phase_3-SQLAlchemy_persistence_foundation_and_mapping_boundaries.md
docs/adr/0014-Phase_3-Database_timestamp_and_audit_metadata_strategy.md
docs/adr/0015-Phase_3-Audit-event-persistence-strategy.md
docs/adr/0016-Phase_3-Clinical-resource-logical-deletion-strategy.md
```

---

## 7. HTTP dependency wiring

### 7.1. Modules

```text
database.py
adapters.py
security.py
use_cases.py
```

### 7.2. Persistence startup flow

```text
Settings.database_url
    -> create_database_engine(...)
        -> create_session_factory(...)
            -> app.state.session_factory
```

### 7.3. Persistence request flow

```text
FastAPI request
    -> get_database_session()
        -> SQLAlchemy Session
            -> SQLAlchemy read adapters
                -> application use-cases
```

The session factory is application-scoped.

The SQLAlchemy `Session` is request-scoped.

### 7.4. Security startup flow

```text
Settings.auth_jwt_secret
Settings.auth_jwt_issuer
Settings.auth_jwt_audience
Settings.auth_jwt_algorithm
    -> JwtTokenVerifier(...)
        -> app.state.jwt_token_verifier
```

The verifier is created once per FastAPI application instance.

It contains verifier configuration, not a current user or request token.

### 7.5. Security request flow

```text
HTTP request
    -> Authorization: Bearer <token>
        -> HTTPBearer(auto_error=False)
            -> get_jwt_token_verifier(request)
                -> request.app.state.jwt_token_verifier
                    -> JwtTokenVerifier.verify(token)
                        -> VerifiedJwtClaims
                            -> CurrentPrincipal
```

`JwtTokenVerifier` is application-scoped.

`CurrentPrincipal` is request-scoped.

### 7.6. Database dependencies

```text
get_session_factory()
get_database_session()
```

`get_session_factory(request)` is currently an ordinary Python call made inside `get_database_session(request)`.

It is not a separate FastAPI `Depends()` node.

`get_database_session()` is a `yield` dependency. It creates a session, yields it to dependent components, and closes it during dependency cleanup.

### 7.7. Security dependencies

```text
get_jwt_token_verifier()
get_current_principal()
```

`get_current_principal()`:

* obtains Bearer credentials
* retrieves the configured verifier
* verifies the token
* translates `VerifiedJwtClaims` into `CurrentPrincipal`
* converts `TokenVerificationError` into `AuthenticationError`

It intentionally does not catch `TokenVerifierConfigurationError`.

### 7.8. Adapter dependencies

```text
get_patient_reader()
get_observation_reader()
get_condition_reader()
get_encounter_reader()
get_audit_event_reader()
```

### 7.9. Use-case dependencies

```text
get_search_patients_use_case()
get_patient_summary_use_case()
get_list_observations_by_code_use_case()
get_export_patient_bundle_use_case()
get_list_audit_events_use_case()
```

### 7.10. Dependency cache

FastAPI normally reuses a dependency result within one request.

When several readers depend on the same `get_database_session`, they receive the same request-scoped session unless caching is explicitly disabled.

### 7.11. Current status

Implemented:

* database session dependency
* adapter dependencies
* use-case dependencies
* JWT verifier dependency
* current-principal dependency

Not implemented:

* RBAC permission model
* permission dependency
* `403 Forbidden`
* protected production routers
* audit actor dependency
* audit write-side composition

---

## 8. Security documentation

Detailed security behavior lives in:

```text
docs/security/README.md
```

The security model decision is recorded in:

```text
docs/adr/0017-Phase_4-MVP SECURITY MODEL. Authentication, RBAC, and Audit Security Model.md
```

The ADR is accepted.

Current implemented authentication flow:

```text
Raw JWT
    -> VerifiedJwtClaims
        -> CurrentPrincipal
```

Next security flow:

```text
CurrentPrincipal.roles
    -> role-to-permission mapping
        -> permission check
            -> allow
            or
            -> 403 Forbidden
```

---

## 9. Local development

Run backend commands from:

```text
apps/api
```

Install locked dependencies:

```bash
pipenv sync --dev
```

Run a command without activating a shell:

```bash
pipenv run <command>
```

---

## 10. Running the API locally

Start from `apps/api`:

```bash
pipenv run uvicorn fhir_gateway.interfaces.http.main:app --reload --app-dir src
```

Application lifecycle:

```text
Uvicorn starts
    -> imports main.py
        -> app = create_app()
            -> settings
            -> logging
            -> database engine
            -> session factory
            -> JWT verifier
            -> FastAPI app
            -> exception handlers
            -> routers
        -> application handles multiple requests
```

Local URL:

```text
http://127.0.0.1:8000
```

Stop with:

```text
CTRL + C
```

---

## 11. Interactive documentation

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

Current OpenAPI only exposes `/health`.

The Bearer dependency exists, but no production endpoint consumes it yet.

---

## 12. Endpoint: Health check

### 12.1. Request

```http
GET /health
```

### 12.2. Response

Status:

```text
200 OK
```

Body:

```json
{
  "status": "ok"
}
```

### 12.3. Security behavior

`/health` is public.

It does not execute:

* database dependencies
* application use-cases
* authentication
* authorization
* clinical access
* audit access

### 12.4. PowerShell

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

### 12.5. curl

```bash
curl http://127.0.0.1:8000/health
```

---

## 13. Error handling

### 13.1. Standard envelope

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "field": "string | null",
    "resource": "string | null",
    "identifier": "string | null"
  }
}
```

Schema location:

```text
apps/api/src/fhir_gateway/interfaces/http/schemas/errors.py
```

Handler location:

```text
apps/api/src/fhir_gateway/interfaces/http/error_handlers.py
```

HTTP-specific errors:

```text
apps/api/src/fhir_gateway/interfaces/http/errors.py
```

### 13.2. Registration

```text
create_app()
    -> register_exception_handlers(app)
```

Registration is application-scoped.

### 13.3. Current mappings

```text
DomainValidationError           -> 400 Bad Request
ApplicationValidationError      -> 400 Bad Request
ApplicationNotFoundError        -> 404 Not Found
AuthenticationError             -> 401 Unauthorized
TokenVerifierConfigurationError -> 500 Internal Server Error
Unexpected Exception            -> 500 Internal Server Error
```

Planned in Sub-issue F:

```text
PermissionDeniedError -> 403 Forbidden
```

### 13.4. Authentication response

Status:

```text
401 Unauthorized
```

Header:

```text
WWW-Authenticate: Bearer
```

Body:

```json
{
  "error": {
    "code": "unauthorized",
    "message": "Authentication credentials are missing or invalid.",
    "field": null,
    "resource": null,
    "identifier": null
  }
}
```

The response does not reveal the technical verification failure.

### 13.5. Planned authorization response

Status:

```text
403 Forbidden
```

Expected body:

```json
{
  "error": {
    "code": "forbidden",
    "message": "The authenticated principal does not have permission to perform this operation.",
    "field": null,
    "resource": null,
    "identifier": null
  }
}
```

A `403` response does not use `WWW-Authenticate: Bearer`, because the caller already has a valid identity.

### 13.6. Verifier configuration failure

Status:

```text
500 Internal Server Error
```

Body:

```json
{
  "error": {
    "code": "internal_server_error",
    "message": "Internal server error.",
    "field": null,
    "resource": null,
    "identifier": null
  }
}
```

The real configuration reason is logged internally.

### 13.7. Framework-generated responses

The project-owned handlers do not yet normalize every FastAPI/Starlette response.

Examples still subject to framework defaults:

```text
unknown-route 404
405 Method Not Allowed
422 request validation
```

These should be reviewed when real Phase 5 request contracts exist.

---

## 14. Testing and quality gate

### 14.1. Full suite

From `apps/api`:

```bash
pipenv run pytest
```

### 14.2. Local quality gate

```bash
pipenv run ruff check src tests
pipenv run pytest
```

### 14.3. HTTP tests

```bash
pipenv run pytest tests/unit/interfaces/http
```

### 14.4. Security tests

```bash
pipenv run pytest tests/unit/infrastructure/security
pipenv run pytest tests/unit/application/security
pipenv run pytest tests/unit/interfaces/http/dependencies/test_security.py
```

### 14.5. Error-handler tests

```bash
pipenv run pytest tests/unit/interfaces/http/test_error_handlers.py
```

### 14.6. Architecture boundary tests

```bash
pipenv run pytest tests/unit/architecture
```

Current boundary tests protect:

* domain/application from SQLAlchemy
* domain/application from FastAPI
* domain/application from PyJWT's `jwt` import namespace

Files:

```text
tests/unit/architecture/test_persistence_boundaries.py
tests/unit/architecture/test_security_boundaries.py
```

The PyPI distribution is named `PyJWT`, but Python imports it as:

```python
import jwt
```

### 14.7. Persistence tests

```bash
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy
```

### 14.8. Alembic inspection

```bash
pipenv run alembic history --verbose
pipenv run alembic heads --verbose
pipenv run alembic upgrade base:head --sql
pipenv run alembic downgrade a6f3c9d2e1b8:d4e8f2a1c9b7 --sql
```

Do not run migrations against PostgreSQL until the local workflow has been explicitly configured.

### 14.9. Current verification rule

Documentation must not claim that the quality gate is green merely because tests and CI configuration exist.

A green state must be based on an actual execution of:

```bash
pipenv run ruff check src tests
pipenv run pytest
```

---

## 15. Continuous integration

Workflow:

```text
.github/workflows/api-ci.yml
```

Name:

```text
API CI
```

Current checks:

```bash
pipenv run ruff check src tests
pipenv run pytest
```

Working directory:

```text
apps/api
```

Runtime:

```text
Python 3.11.9
```

The workflow runs for relevant pull requests and pushes to `main`.

Current CI does not include:

* PostgreSQL service container
* real migration execution
* PostgreSQL integration tests
* mypy
* coverage threshold
* deployment

---

## 16. Current limitations

The API does not yet expose:

* demo token issuing
* patient search
* patient summary
* observation filtering
* bundle export
* audit event listing
* protected production endpoints
* RBAC authorization
* `403 Forbidden`
* audit write pipeline
* clinical request/response schemas
* audit response schemas
* seed data

The API can authenticate a request through a reusable dependency, but no production endpoint consumes it.

The API has no:

* login endpoint
* user database
* password flow
* refresh token
* server-side authentication session
* OIDC/JWKS integration

---

## 17. Planned endpoints

### 17.1. Demo token

```http
POST /auth/demo-token
```

Purpose:

* issue local/demo JWTs for UI and integration testing
* avoid premature user/password infrastructure
* operate only outside production

### 17.2. Patient search

```http
GET /patients?search={text}
```

Use-case:

```text
SearchPatientsUseCase
```

Expected permission:

```text
patient:read
```

### 17.3. Patient summary

```http
GET /patients/{patient_id}/summary
```

Use-case:

```text
GetPatientSummaryUseCase
```

Expected permission:

```text
patient:read
```

### 17.4. Observations by code

```http
GET /patients/{patient_id}/observations?system={system}&code={code}
```

Use-case:

```text
ListObservationsByCodeUseCase
```

Expected permission:

```text
observation:read
```

Code identity uses:

```text
system + code
```

Display text is not the code identity.

### 17.5. Patient bundle export

```http
GET /patients/{patient_id}/bundle
```

Use-case:

```text
ExportPatientBundleUseCase
```

Expected permission:

```text
bundle:export
```

### 17.6. Audit events

```http
GET /audit-events?limit={limit}
```

Use-case:

```text
ListAuditEventsUseCase
```

Expected permission:

```text
audit:read
```

Initial expected behavior:

```text
default limit: 50
maximum limit: 100
newest first
```

---

## 18. Logical deletion API behavior

Logical deletion exists at persistence level.

Affected tables:

```text
patients
observations
conditions
encounters
```

Current API behavior:

* no endpoint exposes `deleted_at`
* no endpoint deletes or restores resources
* no endpoint includes deleted resources explicitly
* ordinary read adapters hide logically deleted resources

Future ordinary clinical endpoints should preserve this behavior.

---

## 19. Audit API behavior

Current audit state:

* `audit_events` table exists
* AuditEvent mapper exists
* AuditEvent reader adapter exists
* `ListAuditEventsUseCase` exists
* HTTP use-case dependency exists
* no audit endpoint exists
* no audit writer exists
* no audit actor dependency exists
* no audit write pipeline exists

Future audit creation must derive:

```text
AuditEvent.agent
```

from trusted runtime context, preferably:

```text
CurrentPrincipal.subject
```

A request body must not choose the audit actor.

---

## 20. API design principles

1. Keep routers thin.
2. Do not put business logic in routers.
3. Do not put persistence logic in routers.
4. Do not parse or verify JWTs in routers.
5. Keep domain independent from HTTP.
6. Keep application independent from HTTP.
7. Keep domain/application independent from SQLAlchemy.
8. Keep domain/application independent from PyJWT.
9. Use infrastructure adapters for application ports.
10. Use HTTP dependencies for runtime composition.
11. Represent the authenticated actor through `CurrentPrincipal`.
12. Require permissions rather than raw role checks in routers.
13. Hide logically deleted resources from ordinary reads.
14. Do not expose technical persistence metadata without an explicit contract.
15. Do not accept user-controlled audit actors.
16. Use the standard API error envelope for project-owned HTTP errors.
17. Keep authentication and authorization centralized.
18. Do not leak JWT, configuration, database, or traceback details.
19. Keep API, security, persistence, ADR, roadmap, and UML documentation aligned.
20. Do not claim quality-gate success without executing it.

---

## 21. Security status

Implemented:

* JWT settings
* HS256 verifier
* required claim validation
* `VerifiedJwtClaims`
* `CurrentPrincipal`
* application-scoped verifier composition
* Bearer credential extraction
* current-principal dependency
* `401 Unauthorized`
* `WWW-Authenticate: Bearer`
* safe verifier-configuration `500`
* security tests
* architecture boundary tests

Not implemented:

* `Role` and `Permission` primitives
* role-to-permission mapping
* authorization helpers
* `PermissionDeniedError`
* `403 Forbidden`
* protected production routers
* audit actor dependency
* audit write pipeline
* demo token endpoint

Production boundary:

The MVP uses local symmetric JWT verification.

Post-MVP security should move toward:

* external OAuth2/OIDC
* asymmetric signing
* JWKS
* key rotation
* secrets management
* revocation/session strategy where required

---

## 22. Related documentation

### Security

```text
docs/security/README.md
```

### Persistence

```text
docs/persistence/README.md
```

### Roadmap

```text
docs/roadmap.md
```

### Security ADR

```text
docs/adr/0017-Phase_4-MVP SECURITY MODEL. Authentication, RBAC, and Audit Security Model.md
```

### HTTP dependency UML

```text
docs/architecture/uml/api/http/dependencies-resolution/
├── annotated-depends-resolution-activity.puml
└── http-dependency-resolution-sequence.puml
```

### HTTP error-handling UML

```text
docs/architecture/uml/api/http/error-handling/
├── http-error-handling-activity.puml
└── http-error-handling-sequence.puml
```

These UML files are living documentation.

Update them when:

* authorization introduces `403 Forbidden`
* permission dependencies are added
* audit actor wiring is introduced
* production endpoints replace conceptual examples
* request validation and framework errors are normalized
