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

Current API status: **Phase 4 / Security foundation in progress**

The API currently exposes one technical endpoint:

* `GET /health`

The backend includes:

* clean FastAPI application structure
* centralized runtime configuration
* logging baseline
* SQLAlchemy/Alembic persistence foundation
* Patient persistence schema
* Patient identifier persistence schema
* Observation code catalog persistence schema
* Condition code catalog persistence schema
* Observation persistence schema
* Condition persistence schema
* Encounter persistence schema
* logical deletion metadata for top-level clinical resources
* AuditEvent persistence schema
* ORM/domain mappers for the current read-side persistence resources
* SQLAlchemy read adapters for the current application ports
* request-scoped SQLAlchemy session management through HTTP dependencies
* HTTP dependency wiring for the current read-side application use-cases
* standard API error response envelope
* HTTP exception handlers for application validation, domain validation, not-found, authentication, JWT verifier configuration, and unexpected errors
* JWT-related runtime settings
* infrastructure-level JWT token verifier
* typed `VerifiedJwtClaims`
* application-level `CurrentPrincipal`
* reusable HTTP Bearer current-principal dependency
* dedicated security documentation entry point
* Ruff quality baseline for the API package
* GitHub Actions API CI workflow for linting and tests

Clinical HTTP endpoints are not implemented yet.

Audit HTTP endpoints are not implemented yet.

Authorization and RBAC dependencies are not implemented yet.

No clinical or audit HTTP endpoint is currently exposed over persistence-backed data.

Persistence-backed read-side dependency wiring is implemented for the current Phase 2 application use-cases.

HTTP Bearer authentication wiring is implemented as a reusable dependency, but it is not yet consumed by production clinical or audit routers because those routers do not exist yet.

A minimal API quality gate is available locally and in GitHub Actions.

Planned future endpoint groups include:

* local/demo token issuing
* patient search
* patient summary
* observation listing by code
* patient bundle export
* audit event listing

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

The long-term goal is to expose a deliberately scoped FHIR-like API over synthetic clinical data, focused on:

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

Current responsibilities:

* `app.py`: creates and configures the FastAPI application, including shared application-state objects such as the SQLAlchemy session factory and JWT token verifier.
* `main.py`: exposes the ASGI `app` object used by Uvicorn.
* `error_handlers.py`: registers HTTP exception handlers and maps internal errors to the standard API error envelope.
* `errors.py`: defines HTTP/interface-layer errors such as `AuthenticationError`.
* `dependencies/database.py`: provides request-scoped SQLAlchemy session access.
* `dependencies/adapters.py`: wires SQLAlchemy read adapters from the current request session.
* `dependencies/use_cases.py`: wires application use-cases from concrete read adapters.
* `dependencies/security.py`: extracts Bearer credentials, verifies JWTs, and builds the current request principal.
* `routers/health.py`: defines the `/health` endpoint.
* `schemas/errors.py`: defines the standard API error response schema.

### 3.3. Boundary rules

The HTTP layer may depend on FastAPI.

The HTTP dependency layer may compose:

* application use-cases
* infrastructure adapters
* SQLAlchemy session management
* JWT security infrastructure

The domain and application layers must not depend on FastAPI.

The domain and application layers must not depend on SQLAlchemy.

The domain and application layers must not depend on PyJWT.

Application and domain errors remain framework-independent.

HTTP error mapping belongs to the HTTP/interface layer.

JWT verification belongs to infrastructure/security.

The application-level current principal must remain independent from FastAPI and PyJWT.

---

## 4. Runtime configuration

### 4.1. Settings location

Runtime settings are defined in:

```text
apps/api/src/fhir_gateway/infrastructure/config/settings.py
```

### 4.2. Current settings

| Setting              | Environment variable              | Default                                                              |
| -------------------- | --------------------------------- | -------------------------------------------------------------------- |
| `app_name`           | `FHIR_GATEWAY_APP_NAME`           | `FHIR Mini-Gateway API`                                              |
| `app_version`        | `FHIR_GATEWAY_APP_VERSION`        | `0.1.0`                                                              |
| `environment`        | `FHIR_GATEWAY_ENVIRONMENT`        | `local`                                                              |
| `log_level`          | `FHIR_GATEWAY_LOG_LEVEL`          | `INFO`                                                               |
| `database_url`       | `FHIR_GATEWAY_DATABASE_URL`       | `postgresql+psycopg://postgres:postgres@localhost:5432/fhir_gateway` |
| `auth_jwt_secret`    | `FHIR_GATEWAY_AUTH_JWT_SECRET`    | `None`                                                               |
| `auth_jwt_issuer`    | `FHIR_GATEWAY_AUTH_JWT_ISSUER`    | `fhir-gateway-local`                                                 |
| `auth_jwt_audience`  | `FHIR_GATEWAY_AUTH_JWT_AUDIENCE`  | `fhir-gateway-api`                                                   |
| `auth_jwt_algorithm` | `FHIR_GATEWAY_AUTH_JWT_ALGORITHM` | `HS256`                                                              |

### 4.3. Allowed environment values

```text
local
test
development
production
```

### 4.4. Allowed log level values

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

Secrets shown in examples must only be used for local/demo purposes.

Do not commit a real secret to the repository.

### 4.6. Configuration principle

Settings are loaded through `pydantic-settings`.

Runtime configuration is centralized so that infrastructure concerns such as logging, database connectivity, and JWT verification do not define their own scattered environment-variable logic.

Security settings are implemented as part of the Phase 4 security foundation.

Security settings are documented in:

```text
docs/security/README.md
```

---

## 5. Logging

### 5.1. Logging location

Basic logging is configured in:

```text
apps/api/src/fhir_gateway/infrastructure/logging.py
```

### 5.2. Current format

```text
%(asctime)s %(levelname)s [%(name)s] %(message)s
```

### 5.3. Example output

```text
2026-05-18 10:30:00 INFO [fhir_gateway.interfaces.http.app] Creating FastAPI application for environment: local
```

### 5.4. Logging behavior

Logging is configured during FastAPI application creation using the configured `FHIR_GATEWAY_LOG_LEVEL`.

Unexpected HTTP errors are logged internally by the HTTP error handler before returning a safe generic `500 Internal Server Error` response.

JWT verifier configuration errors are also logged internally before returning a generic `500 Internal Server Error` response.

Sensitive JWT contents, signing secrets, and detailed token-verification failures must not be exposed to API clients.

---

## 6. Persistence status

### 6.1. Current persistence foundation

The backend includes a SQLAlchemy/Alembic persistence foundation.

Current persistence status:

* Patient ORM schema exists.
* Patient identifier ORM schema exists.
* Observation code catalog ORM schema exists.
* Condition code catalog ORM schema exists.
* Observation ORM schema exists.
* Condition ORM schema exists.
* Encounter ORM schema exists.
* Top-level clinical resources include logical deletion metadata through `deleted_at`.
* AuditEvent ORM schema exists.
* ORM/domain mappers exist for current read-side persistence resources.
* SQLAlchemy read adapters exist for current application ports.
* Request-scoped SQLAlchemy session management exists through HTTP dependencies.
* Application use-case dependency wiring exists for current read-side use-cases.
* No clinical HTTP endpoint uses persistence yet.
* No audit HTTP endpoint uses persistence yet.

### 6.2. Logical deletion metadata

Current top-level clinical resource tables with logical deletion metadata:

* `patients.deleted_at`
* `observations.deleted_at`
* `conditions.deleted_at`
* `encounters.deleted_at`

### 6.3. Audit table

Current audit table:

* `audit_events`

The API does not expose `deleted_at` through HTTP responses at this stage.

The API does not expose `audit_events` through HTTP at this stage.

### 6.4. Current Alembic migration chain

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

Persistence details are documented separately in:

```text
docs/persistence/README.md
```

Logical deletion strategy is documented in:

```text
docs/adr/0016-clinical-resource-logical-deletion-strategy.md
```

AuditEvent persistence strategy is documented in:

```text
docs/adr/0015-audit-event-persistence-strategy.md
```

---

## 7. HTTP dependency wiring

### 7.1. Current dependency layer

The API includes HTTP dependency wiring for:

* persistence-backed read use-cases
* Bearer-token authentication
* current-principal construction

This wiring is intentionally located in:

```text
apps/api/src/fhir_gateway/interfaces/http/dependencies/
```

### 7.2. Current dependency modules

```text
database.py
adapters.py
security.py
use_cases.py
```

### 7.3. Dependency responsibilities

Responsibilities:

* `database.py` provides request-scoped SQLAlchemy session access.
* `adapters.py` builds SQLAlchemy read adapters from the current request session.
* `use_cases.py` builds application use-cases from those adapters.
* `security.py` extracts Bearer credentials, retrieves the shared JWT verifier, verifies the token, and constructs `CurrentPrincipal`.

### 7.4. Persistence runtime flow

```text
FastAPI request
    -> get_database_session()
        -> SQLAlchemy Session
            -> SQLAlchemy read adapters
                -> application use-cases
```

### 7.5. Persistence application-startup flow

The application startup flow prepares the session factory:

```text
Settings.database_url
    -> create_database_engine(...)
    -> create_session_factory(...)
    -> app.state.session_factory
```

The request flow then uses that factory:

```text
request
    -> request.app
        -> request.app.state.session_factory
            -> Session for the current request
```

### 7.6. Security application-startup flow

The application startup flow also prepares the JWT token verifier:

```text
Settings.auth_jwt_secret
Settings.auth_jwt_issuer
Settings.auth_jwt_audience
Settings.auth_jwt_algorithm
    -> JwtTokenVerifier(...)
        -> app.state.jwt_token_verifier
```

The verifier is created once per FastAPI application instance.

The verifier does not represent a user and does not contain the current request token.

The verifier is shared by requests handled by that application instance.

### 7.7. Security request flow

A protected HTTP request uses the configured verifier through the security dependency:

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

The `JwtTokenVerifier` is application-scoped.

The `CurrentPrincipal` is request-scoped.

A new `CurrentPrincipal` is created for each successfully authenticated request.

### 7.8. Current request-scoped database dependency

The current request-scoped database dependency is:

```text
get_database_session()
```

It creates one SQLAlchemy `Session` for the current dependency execution and closes it when the request finishes.

The session factory is shared.

The SQLAlchemy `Session` is not shared between requests.

### 7.9. Current security dependencies

Current security dependencies:

```text
get_jwt_token_verifier()
get_current_principal()
```

Responsibilities:

```text
get_jwt_token_verifier()
    -> retrieves the application-scoped verifier

get_current_principal()
    -> extracts Bearer credentials
    -> verifies the token
    -> converts VerifiedJwtClaims into CurrentPrincipal
```

### 7.10. Current adapter dependencies

The current adapter dependencies are:

```text
get_patient_reader()
get_observation_reader()
get_condition_reader()
get_encounter_reader()
get_audit_event_reader()
```

### 7.11. Current use-case dependencies

The current use-case dependencies are:

```text
get_search_patients_use_case()
get_patient_summary_use_case()
get_list_observations_by_code_use_case()
get_export_patient_bundle_use_case()
get_list_audit_events_use_case()
```

### 7.12. Dependency boundary rule

Routers must not instantiate the following objects manually:

* SQLAlchemy sessions
* SQLAlchemy adapters
* application use-cases
* JWT token verifiers

Routers should receive already-wired use-cases and security context through FastAPI dependencies.

Protected endpoints should request `CurrentPrincipal` or a future permission dependency rather than parse JWTs directly.

Domain and application layers remain independent from FastAPI, PyJWT, and SQLAlchemy.

### 7.13. Current status

Current status:

* request-scoped SQLAlchemy session dependency: implemented
* SQLAlchemy read adapter dependencies: implemented
* application use-case dependencies: implemented
* API error response envelope: implemented
* HTTP exception handler foundation: implemented
* authentication error mapping: implemented
* token-verifier configuration error mapping: implemented
* HTTP Bearer current-principal dependency: implemented
* clinical routers: not implemented yet
* audit routers: not implemented yet
* authorization/RBAC dependencies: not implemented yet
* `403 Forbidden` mapping: not implemented yet
* clinical Pydantic request/response schemas: not implemented yet
* audit Pydantic response schemas: not implemented yet

Clinical and audit endpoints remain intentionally deferred until endpoint contracts, response schemas, authorization rules, and error mappings are designed.

---

## 8. Security documentation

### 8.1. Current security status

The HTTP authentication foundation is implemented.

Current implemented flow:

```text
Authorization: Bearer <token>
    -> JwtTokenVerifier
        -> VerifiedJwtClaims
            -> CurrentPrincipal
```

The current `/health` endpoint is public.

Future clinical and audit endpoints should not be treated as public by default.

Authorization and RBAC are not implemented yet.

Phase 4 continues with:

* role-to-permission mapping
* permission checks
* `403 Forbidden`
* audit actor derivation
* security and audit dependency wiring

### 8.2. Security documentation location

Security behavior is documented separately in:

```text
docs/security/README.md
```

That document covers:

* Bearer-token-based authentication
* JWT requirements
* token verification
* current-principal semantics
* roles
* permissions
* authorization flow
* `401 Unauthorized`
* planned `403 Forbidden`
* public vs protected endpoints
* audit actor derivation
* security error behavior
* security settings
* MVP limitations
* post-MVP backlog references

### 8.3. Security ADR

The MVP security model is defined by:

```text
docs/adr/0017-mvp-authentication-rbac-and-audit-security-model.md
```

### 8.4. Security and API error envelope

Authentication errors use the standard API error response envelope.

Current mapping:

```text
Missing or invalid token -> 401 Unauthorized
```

Planned authorization mapping:

```text
Missing permission -> 403 Forbidden
```

A JWT verifier configuration problem is a server error:

```text
JWT verifier misconfiguration -> 500 Internal Server Error
```

It must not be translated into `401 Unauthorized`.

---

## 9. Local development

### 9.1. Working directory

Run all backend commands from:

```text
apps/api
```

### 9.2. Activate Pipenv environment

Activate the Pipenv environment:

```bash
pipenv shell
```

Or run commands directly:

```bash
pipenv run <command>
```

### 9.3. Install dependencies

Install dependencies:

```bash
pipenv install
```

Install dependencies exactly from the lockfile:

```bash
pipenv sync --dev
```

Use `pipenv sync --dev` especially in reproducible environments such as CI, because it installs the locked dependency set from `Pipfile.lock`, including development tools such as Ruff and pytest.

---

## 10. Running the API locally

### 10.1. Source layout

Because the backend uses a `src/` layout, the package lives under:

```text
apps/api/src/fhir_gateway
```

### 10.2. Start command

Run the API from `apps/api` with:

```bash
pipenv run uvicorn fhir_gateway.interfaces.http.main:app --reload --app-dir src
```

### 10.3. Application lifecycle

Uvicorn imports:

```text
fhir_gateway.interfaces.http.main
```

That module executes:

```text
app = create_app()
```

The FastAPI application is created when the server process starts.

It is not recreated for every HTTP request.

Conceptual lifecycle:

```text
Uvicorn process starts
    -> imports main.py
        -> create_app()
            -> settings
            -> logging
            -> SQLAlchemy engine
            -> session factory
            -> JWT token verifier
            -> FastAPI application
            -> exception handlers
            -> routers
        -> application remains alive
            -> request 1
            -> request 2
            -> request 3
```

With multiple Uvicorn workers, each worker process owns its own FastAPI application instance.

With development reload enabled, changing source code may restart the process and create a new application instance.

### 10.4. Local URL

The API starts at:

```text
http://127.0.0.1:8000
```

### 10.5. Stop command

Stop the server with:

```text
CTRL + C
```

---

## 11. Interactive documentation

### 11.1. Swagger UI

FastAPI exposes interactive API documentation automatically.

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

### 11.2. ReDoc

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

### 11.3. Current OpenAPI status

At the current stage, these pages only expose `/health`.

The reusable Bearer security dependency exists, but no production protected router consumes it yet.

Future clinical and audit endpoints will appear once routers and HTTP schemas are implemented.

---

## 12. Endpoint: Health check

### 12.1. `GET /health`

Checks whether the API process is alive and responding.

This is a public technical endpoint.

It does not access:

* domain entities
* application use-cases
* database
* authentication
* authorization
* clinical data
* audit data

### 12.2. Request

```http
GET /health
```

### 12.3. Successful response

Status code:

```text
200 OK
```

Body:

```json
{
  "status": "ok"
}
```

### 12.4. Browser example

Open:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

### 12.5. PowerShell example

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

### 12.6. curl example

```bash
curl http://127.0.0.1:8000/health
```

---

## 13. Error handling

### 13.1. Standard API error response envelope

The API defines a standard error response envelope:

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

This envelope is defined in the HTTP/interface layer.

The domain and application layers remain independent from FastAPI and HTTP response details.

### 13.2. Error schema location

The error response schema is located in:

```text
apps/api/src/fhir_gateway/interfaces/http/schemas/errors.py
```

The main schema types are:

```text
ApiError
ApiErrorResponse
```

### 13.3. Exception handler location

HTTP exception handlers are located in:

```text
apps/api/src/fhir_gateway/interfaces/http/error_handlers.py
```

HTTP-specific authentication errors are defined in:

```text
apps/api/src/fhir_gateway/interfaces/http/errors.py
```

### 13.4. Handler registration

Exception handlers are registered when the FastAPI application starts:

```text
create_app()
    -> register_exception_handlers(app)
```

FastAPI stores the mapping between exception types and handler functions.

This registration does not happen once per request.

When an exception propagates during a request, FastAPI selects the most appropriate registered handler.

### 13.5. Current mappings

Current mappings:

```text
DomainValidationError           -> 400 Bad Request
ApplicationValidationError      -> 400 Bad Request
ApplicationNotFoundError        -> 404 Not Found
AuthenticationError             -> 401 Unauthorized
TokenVerifierConfigurationError -> 500 Internal Server Error
Unexpected Exception            -> 500 Internal Server Error
```

Future security mapping:

```text
Missing permission -> 403 Forbidden
```

`AuthenticationError` represents missing or invalid Bearer credentials.

`TokenVerifierConfigurationError` represents incorrect server-side JWT verifier configuration.

It must not be translated into `401 Unauthorized`.

### 13.6. Error-response construction flow

All custom handlers use the same response builder:

```text
exception handler
    -> _build_error_response(...)
        -> ApiError
            -> ApiErrorResponse
                -> model_dump()
                    -> JSONResponse
```

This centralizes:

* HTTP status code
* API error code
* public error message
* field metadata
* resource metadata
* identifier metadata
* optional response headers

### 13.7. Validation error example

Status:

```text
400 Bad Request
```

Body:

```json
{
  "error": {
    "code": "validation_error",
    "message": "cannot be empty",
    "field": "Code.code",
    "resource": null,
    "identifier": null
  }
}
```

### 13.8. Not-found error example

Status:

```text
404 Not Found
```

Body:

```json
{
  "error": {
    "code": "not_found",
    "message": "Patient not found: pat-001",
    "field": null,
    "resource": "Patient",
    "identifier": "pat-001"
  }
}
```

### 13.9. Authentication error example

Status:

```text
401 Unauthorized
```

Headers:

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

Authentication errors intentionally do not reveal whether the token:

* was expired
* was malformed
* had an invalid signature
* had the wrong issuer
* had the wrong audience
* lacked required claims
* contained invalid claim shapes

### 13.10. JWT verifier configuration error example

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

The real configuration problem is logged internally.

The response must not reveal details such as:

```text
JWT secret is not configured.
JWT secret must be at least 32 bytes long.
```

### 13.11. Unexpected internal server error example

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

Unexpected errors are logged internally with traceback information.

Internal implementation details must not be leaked to API clients.

### 13.12. Current FastAPI default errors

The custom handlers currently cover project-owned exceptions registered in `error_handlers.py`.

Framework-generated responses such as the following may still use FastAPI or Starlette defaults:

```text
404 for an unknown HTTP route
405 Method Not Allowed
422 request validation error
```

These responses should be reviewed when Phase 5 introduces real request parameters, path parameters, query parameters, and response schemas.

A future hardening step may normalize them into the standard API error envelope.

---

## 14. Testing and quality gate

### 14.1. Full test suite

Run the full test suite from `apps/api`:

```bash
pipenv run pytest
```

### 14.2. Local API quality gate

Run the local API quality gate from `apps/api`:

```bash
pipenv run ruff check src tests
pipenv run pytest
```

This is the local equivalent of the GitHub Actions API CI workflow.

The quality gate currently checks:

* Ruff linting for `src` and `tests`
* the full pytest suite
* architecture boundary tests as part of pytest
* HTTP error response envelope tests
* JWT token-verifier tests
* `CurrentPrincipal` tests
* HTTP authentication dependency tests

The quality gate does not yet run:

* mypy
* coverage threshold enforcement
* PostgreSQL integration tests
* Alembic migrations against a real PostgreSQL database
* deployment checks

### 14.3. HTTP tests

Run HTTP tests:

```bash
pipenv run pytest tests/unit/interfaces/http
```

Run HTTP dependency tests:

```bash
pipenv run pytest tests/unit/interfaces/http/dependencies
```

Run HTTP error-handler tests:

```bash
pipenv run pytest tests/unit/interfaces/http/test_error_handlers.py
```

Run HTTP application-composition tests:

```bash
pipenv run pytest tests/unit/interfaces/http/test_app.py
```

### 14.4. Security tests

Run infrastructure JWT verifier tests:

```bash
pipenv run pytest tests/unit/infrastructure/security
```

Run current-principal tests:

```bash
pipenv run pytest tests/unit/application/security
```

Run HTTP security dependency tests:

```bash
pipenv run pytest tests/unit/interfaces/http/dependencies/test_security.py
```

### 14.5. Settings and logging tests

Run settings tests:

```bash
pipenv run pytest tests/unit/infrastructure/config/test_settings.py
```

Run logging tests:

```bash
pipenv run pytest tests/unit/infrastructure/test_logging.py
```

### 14.6. Architecture boundary tests

Run architecture boundary tests:

```bash
pipenv run pytest tests/unit/architecture
```

These tests protect project boundaries, especially the rules that:

* domain and application must remain independent from FastAPI
* domain and application must remain independent from SQLAlchemy
* domain and application must remain independent from PyJWT

### 14.7. Persistence tests

Run persistence tests:

```bash
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy
```

Run ORM model tests:

```bash
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models
```

Run Patient ORM model tests:

```bash
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models/test_patient_orm_models.py
```

Run clinical resource ORM model tests:

```bash
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models/test_clinical_resource_orm_models.py
```

Run AuditEvent ORM model tests:

```bash
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/models/test_audit_event_orm_models.py
```

Run ORM/domain mapper tests:

```bash
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/mappers
```

Run SQLAlchemy adapter tests:

```bash
pipenv run pytest tests/unit/infrastructure/persistence/sqlalchemy/adapters
```

### 14.8. Alembic inspection commands

Useful Alembic inspection commands:

```bash
pipenv run alembic history --verbose
pipenv run alembic heads --verbose
pipenv run alembic upgrade head --sql
pipenv run alembic upgrade base:head --sql
pipenv run alembic downgrade a6f3c9d2e1b8:d4e8f2a1c9b7 --sql
```

Do not run database migrations against PostgreSQL until a local PostgreSQL workflow has been created and configured.

---

## 15. Continuous integration

### 15.1. Workflow file

The API package includes a GitHub Actions workflow:

```text
.github/workflows/api-ci.yml
```

The workflow is named:

```text
API CI
```

### 15.2. Purpose

The workflow runs the backend quality gate automatically for API-related changes.

Current workflow checks:

```bash
pipenv run ruff check src tests
pipenv run pytest
```

The workflow runs from:

```text
apps/api
```

The workflow installs dependencies through Pipenv using the locked dependency set.

### 15.3. Triggers

The workflow is triggered for:

* pull requests that modify `apps/api/**` or the workflow file itself
* pushes to `main` that modify `apps/api/**` or the workflow file itself

### 15.4. What happens if CI fails?

If GitHub Actions detects a Ruff error or test failure after a push:

* the push is not automatically cancelled
* the commit remains in the remote branch
* the workflow run is marked as failed
* the repository shows a red failing check for that commit
* a later fix commit or revert is needed to make the branch green again

CI reports whether the pushed code passes the quality gate.

It does not undo the push by itself.

If branch protection rules are configured later, GitHub can prevent merging Pull Requests unless the workflow is green.

If direct pushes to `main` are restricted later, GitHub can enforce stricter rules before changes reach `main`.

### 15.5. Current CI limitations

This CI baseline is intentionally minimal.

It does not yet include:

* PostgreSQL service containers
* real database migration execution
* integration tests against PostgreSQL
* type checking with mypy
* coverage thresholds
* deployment steps

Those checks can be added later when the project needs them.

---

## 16. Current limitations

The API does not yet expose:

* local/demo token issuing
* patient search
* patient summary retrieval
* observation filtering
* bundle export
* audit event listing
* protected clinical endpoints
* protected audit endpoints
* authorization/RBAC
* persistence-backed clinical endpoints
* persistence-backed audit endpoints
* clinical Pydantic request/response schemas
* audit Pydantic response schemas
* seed data

The API can authenticate a request through a reusable dependency, but no production endpoint currently consumes that dependency.

The API has no login endpoint, user database, password flow, refresh token, or server-side authentication session.

The API already contains read-side wiring for the current application use-cases, but no production router consumes that wiring yet.

These capabilities are intentionally deferred.

---

## 17. Planned endpoints

The following endpoints are planned but not implemented yet.

### 17.1. Local/demo token endpoint

```http
POST /auth/demo-token
```

Purpose:

* issue a local/demo JWT for UI and integration testing
* avoid implementing database-backed users or password authentication for the MVP
* support local, test, or demo environments only

The endpoint must not act as production authentication.

It must be disabled or rejected in production.

### 17.2. Patient search

```http
GET /patients?search={text}
```

Related use-case:

```text
SearchPatientsUseCase
```

Current persistence/wiring status:

* Patient ORM schema exists.
* Patient ORM/domain mapper exists.
* SQLAlchemy patient reader/search adapter exists.
* HTTP dependency wiring for `SearchPatientsUseCase` exists.
* HTTP endpoint is not implemented yet.

Expected security behavior:

* protected endpoint
* expected permission: `patient:read`

Expected persistence behavior:

* should query `patients`
* should search by patient id, patient name fields, and patient identifiers where supported by the adapter
* should hide logically deleted patients by default using `patients.deleted_at IS NULL`

### 17.3. Patient summary

```http
GET /patients/{patient_id}/summary
```

Related use-case:

```text
GetPatientSummaryUseCase
```

Current persistence/wiring status:

* Patient, Observation, Condition, and Encounter ORM schemas exist.
* ORM/domain mappers exist for the involved resources.
* SQLAlchemy read adapters exist for the involved resources.
* HTTP dependency wiring for `GetPatientSummaryUseCase` exists.
* HTTP endpoint is not implemented yet.

Expected security behavior:

* protected endpoint
* expected permission: `patient:read`

Expected persistence behavior:

* should query Patient data
* should include related Observations, Conditions, and Encounters
* should hide logically deleted resources by default

### 17.4. Observations by code

```http
GET /patients/{patient_id}/observations?system={system}&code={code}
```

Related use-case:

```text
ListObservationsByCodeUseCase
```

Clinical code identity should be based on:

* `system`
* `code`

The display text should not be used as the code identity.

Current persistence/wiring status:

* Observation ORM schema exists.
* Observation code catalog ORM schema exists.
* Observation ORM/domain mapper exists.
* SQLAlchemy observation reader/by-code adapter exists.
* HTTP dependency wiring for `ListObservationsByCodeUseCase` exists.
* HTTP endpoint is not implemented yet.

Expected security behavior:

* protected endpoint
* expected permission: `observation:read`

Expected persistence behavior:

* should query `observations`
* should join or resolve `observation_codes`
* should hide logically deleted observations by default

### 17.5. Patient bundle export

```http
GET /patients/{patient_id}/bundle
```

Related use-case:

```text
ExportPatientBundleUseCase
```

The application layer returns a `PatientBundle` application model.

Final HTTP JSON serialization will be handled in the API/interface layer.

Current persistence/wiring status:

* Patient, Observation, Condition, and Encounter ORM schemas exist.
* ORM/domain mappers exist for the involved resources.
* SQLAlchemy read adapters exist for the involved resources.
* HTTP dependency wiring for `ExportPatientBundleUseCase` exists.
* HTTP endpoint is not implemented yet.

Expected security behavior:

* protected endpoint
* expected permission: `bundle:export`

Expected persistence behavior:

* should export the patient bundle from persistence-backed data
* should exclude logically deleted resources by default for ordinary clinical reads unless a later design explicitly says otherwise

### 17.6. Audit events

```http
GET /audit-events?limit={limit}
```

Related use-case:

```text
ListAuditEventsUseCase
```

Initial expected behavior:

* default limit: `50`
* maximum limit: `100`
* ordered from newest to oldest

Current persistence/wiring status:

* `audit_events` table exists
* AuditEvent ORM/domain mapper exists
* SQLAlchemy audit event reader adapter exists
* HTTP dependency wiring for `ListAuditEventsUseCase` exists
* HTTP endpoint is not implemented yet

Expected security behavior:

* protected endpoint
* expected permission: `audit:read`

Advanced audit filtering and pagination are deferred.

---

## 18. Logical deletion API behavior

### 18.1. Current logical deletion status

Logical deletion has been introduced at the persistence-schema level.

Affected tables:

* `patients`
* `observations`
* `conditions`
* `encounters`

### 18.2. Current API behavior

Current API behavior:

* no endpoint exposes `deleted_at`
* no endpoint performs logical deletion
* no endpoint restores logically deleted resources
* no endpoint includes deleted resources by explicit option
* no clinical endpoint is currently exposed over persistence-backed data

### 18.3. Current persistence adapter behavior

Current persistence adapter behavior:

* ordinary read adapters hide logically deleted top-level clinical resources by default

Future ordinary clinical endpoints should preserve that behavior and hide logically deleted resources by default.

Future admin/audit endpoints may decide whether deleted resources can be queried explicitly.

The exact HTTP response behavior for logically deleted resources, such as `404 Not Found`, will be decided when persistence-backed endpoints are implemented.

---

## 19. Audit API behavior

### 19.1. Current audit persistence status

AuditEvent persistence exists at the database-schema level.

Current table:

```text
audit_events
```

### 19.2. Current API behavior

Current API behavior:

* no `/audit-events` endpoint exists yet
* no audit write pipeline exists yet
* no protected clinical endpoint exists yet
* no audit actor dependency is wired to production endpoints yet

### 19.3. Current read-side wiring status

Current read-side wiring status:

* `ListAuditEventsUseCase` exists
* SQLAlchemy audit event reader adapter exists
* HTTP dependency wiring for audit event listing exists
* audit events would be read from persistence once an endpoint consumes the dependency

Future audit listing should use:

```text
ListAuditEventsUseCase
```

and return audit events ordered from newest to oldest.

### 19.4. Future audit actor rule

Future audit creation must not allow arbitrary user-controlled request bodies to decide the `agent` value.

The `agent` should come from trusted runtime context.

For authenticated human requests, the preferred source is:

```text
CurrentPrincipal.subject
```

Other future trusted actor types may include:

* system identity
* background job identity
* local/demo identity
* AI-assisted workflow identity

Security-specific audit actor behavior is documented in:

```text
docs/security/README.md
```

---

## 20. API design principles

As the API evolves:

1. Keep routers thin.
2. Do not put business logic in routers.
3. Do not put persistence logic in routers.
4. Do not parse or verify JWTs directly in routers.
5. Keep domain independent from HTTP.
6. Keep application independent from HTTP.
7. Keep domain independent from SQLAlchemy.
8. Keep application independent from SQLAlchemy.
9. Keep domain and application independent from PyJWT.
10. Use infrastructure adapters to implement application ports.
11. Use HTTP dependencies as the runtime composition layer for sessions, adapters, use-cases, authentication, and authorization.
12. Represent the authenticated actor through `CurrentPrincipal`.
13. Require permissions rather than scattering raw role checks in routers.
14. Preserve structured clinical evidence in API responses.
15. Avoid broad generic repositories until repeated adapter needs justify them.
16. Hide logically deleted clinical resources from ordinary reads by default.
17. Do not expose technical persistence metadata unless explicitly designed.
18. Do not let arbitrary request input define audit `agent`.
19. Keep the local quality gate and CI workflow aligned.
20. Use the standard API error response envelope for exposed HTTP errors.
21. Keep authentication and authorization behavior centralized in HTTP dependencies.
22. Do not leak JWT, configuration, database, or stack-trace details to clients.
23. Keep detailed security behavior documented in `docs/security/README.md`.
24. Update architecture diagrams when request flows or exception mappings change.

---

## 21. Security status

### 21.1. Current status

The HTTP authentication foundation is implemented.

Implemented:

* JWT runtime settings
* JWT token verifier
* `VerifiedJwtClaims`
* application-level `CurrentPrincipal`
* application-scoped JWT verifier composition
* Bearer credential extraction
* HTTP current-principal dependency
* `401 Unauthorized` mapping for missing or invalid credentials
* `WWW-Authenticate: Bearer` response header
* safe `500 Internal Server Error` mapping for JWT verifier configuration errors
* generic security messages that avoid leaking token-verification details
* authentication tests

Not implemented yet:

* role-to-permission mapping
* RBAC authorization helpers
* permission dependencies
* `403 Forbidden`
* protected clinical routers
* protected audit routers
* local/demo token issuing endpoint
* audit write pipeline
* trusted audit actor wiring to protected operations

The current `/health` endpoint is public.

Future clinical and audit endpoints should not be treated as public by default.

### 21.2. Authentication flow

Current implemented flow:

```text
Authorization: Bearer <token>
    -> HTTPBearer(auto_error=False)
        -> JwtTokenVerifier.verify(token)
            -> VerifiedJwtClaims
                -> CurrentPrincipal
```

### 21.3. Error distinction

```text
Missing or invalid credentials
    -> AuthenticationError
        -> 401 Unauthorized

Invalid JWT verifier configuration
    -> TokenVerifierConfigurationError
        -> 500 Internal Server Error
```

The distinction is intentional:

```text
401
    -> the request did not present valid credentials

500
    -> the server security configuration is invalid
```

### 21.4. Security documentation

Security documentation is located in:

```text
docs/security/README.md
```

### 21.5. Security model ADR

The MVP security model is defined in:

```text
docs/adr/0017-mvp-authentication-rbac-and-audit-security-model.md
```

### 21.6. Production boundary

The current MVP uses local symmetric JWT verification through HS256.

This is not a complete production identity platform.

Post-MVP security should move toward:

* external OAuth2/OIDC
* asymmetric signing
* JWKS validation
* key rotation
* production secrets management
* revocation or session strategy where required

---

## 22. Related documentation

### 22.1. Persistence documentation

```text
docs/persistence/README.md
```

### 22.2. Security documentation

```text
docs/security/README.md
```

### 22.3. Error-handling UML diagrams

Current Phase 4 error-flow diagrams may be stored in:

```text
docs/architecture/uml/phase-4/error-handling/
```

Suggested files:

```text
http-error-handling-sequence.puml
http-error-handling-activity.puml
```

These diagrams are living Phase 4 documentation and should be updated when authorization and endpoint-level errors are introduced.

### 22.4. Related ADRs

Related ADRs:

* ADR 0011: HTTP API structure and runtime composition
* ADR 0012: SQLAlchemy persistence foundation and mapping boundaries
* ADR 0013: Centralized runtime configuration
* ADR 0014: Database timestamp and audit metadata strategy
* ADR 0015: AuditEvent persistence strategy
* ADR 0016: Clinical resource logical deletion strategy
* ADR 0017: MVP authentication, RBAC, and audit security model
