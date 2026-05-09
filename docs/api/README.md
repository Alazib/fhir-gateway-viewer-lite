# FHIR Mini-Gateway API Documentation

## Status

Current API status: **Phase 3 / Backend foundation**

The API currently exposes only the initial technical health endpoint.

Clinical endpoints are not implemented yet in this phase.

Current available endpoint:

- `GET /health`

Planned future endpoint groups include:

- patient search
- patient summary
- observation listing by code
- patient bundle export
- audit event listing

Those endpoints will be added in later phases after the backend foundation, persistence, adapters, and HTTP wiring are properly established.

---

## API purpose

The FHIR Mini-Gateway API is the backend interface for the `FHIR Gateway Viewer Lite` project.

Its long-term purpose is to expose a deliberately scoped FHIR-like API for synthetic clinical data, including:

- patients
- observations
- conditions
- encounters
- audit events
- patient-centered export bundles

The API is designed as part of a portfolio-grade Health IT project focused on:

- clean architecture
- healthcare interoperability concepts
- strongly structured clinical data
- traceability
- future EHR-lite viewer integration
- future grounded Applied AI Engineering features

This API is not intended to process real patient data.

Only synthetic/demo data should be used.

---

## Current architecture position

The API belongs to the `interfaces/http` layer.

Current HTTP structure:

    apps/api/src/fhir_gateway/interfaces/http/
    ├── __init__.py
    ├── app.py
    ├── main.py
    └── routers/
        ├── __init__.py
        └── health.py

Responsibilities:

- `app.py`: creates and configures the FastAPI application.
- `main.py`: exposes the ASGI `app` object used by Uvicorn.
- `routers/health.py`: defines the `/health` endpoint.

The HTTP layer may depend on FastAPI.

The domain and application layers must not depend on FastAPI.

---

## Local development requirements

Run all commands from:

    apps/api

The project currently uses Pipenv.

Activate the environment with:

    pipenv shell

Or run commands directly with:

    pipenv run <command>

---

## Running the API locally

Because the backend uses a `src/` layout, the application package lives under:

    apps/api/src/fhir_gateway

For that reason, Uvicorn must be told where the application package is located.

Run the API from `apps/api` with:

    pipenv run uvicorn fhir_gateway.interfaces.http.main:app --reload --app-dir src

The API will start at:

    http://127.0.0.1:8000

Expected Uvicorn output includes:

    Uvicorn running on http://127.0.0.1:8000

To stop the server, press:

    CTRL + C

---

## Why `--app-dir src` is required

The project uses this source layout:

    apps/api/
    └── src/
        └── fhir_gateway/

When running:

    uvicorn fhir_gateway.interfaces.http.main:app

Uvicorn needs to import:

    fhir_gateway.interfaces.http.main

Without `--app-dir src`, Python may not find the `fhir_gateway` package because it is not located directly under `apps/api`.

This command fixes the import path:

    pipenv run uvicorn fhir_gateway.interfaces.http.main:app --reload --app-dir src

---

## Interactive API documentation

FastAPI automatically exposes interactive API documentation.

After starting the server, open:

    http://127.0.0.1:8000/docs

This opens the Swagger UI.

Alternative documentation is available at:

    http://127.0.0.1:8000/redoc

At the current stage, these pages only show the `/health` endpoint.

They will grow as clinical and audit endpoints are added in later phases.

---

## Current endpoint: Health check

### `GET /health`

Checks whether the API process is alive and responding.

This is a technical endpoint.

It does not access the domain layer, application use-cases, database, persistence, authentication, or clinical data.

### Request

    GET /health

### Successful response

Status code:

    200 OK

Body:

    {
      "status": "ok"
    }

### Example using browser

Open:

    http://127.0.0.1:8000/health

Expected response:

    {
      "status": "ok"
    }

### Example using PowerShell

    Invoke-RestMethod http://127.0.0.1:8000/health

Expected result:

    status
    ------
    ok

### Example using curl

    curl http://127.0.0.1:8000/health

Expected result:

    {"status":"ok"}

---

## Health endpoint semantics

The `/health` endpoint currently verifies only that the API application is running.

It does not yet check:

- database connectivity
- migrations status
- external services
- authentication services
- background workers
- storage availability

A deeper health or readiness check may be introduced later if needed.

Possible future endpoints:

- `/health`
- `/ready`
- `/live`

For now, only `/health` exists.

---

## Testing the API layer

Run the HTTP health tests from `apps/api`:

    pipenv run pytest tests/unit/interfaces/http/test_health.py

Run the full backend test suite:

    pipenv run pytest

The current health tests verify that:

- `GET /health` returns HTTP `200`
- `GET /health` returns `{"status": "ok"}`

---

## Current API limitations

At the current Phase 3 stage, the API does not yet expose:

- patient search
- patient summary retrieval
- observation filtering
- bundle export
- audit event listing
- authentication
- authorization
- persistence-backed data
- application use-case wiring through HTTP
- API error response envelope
- Pydantic request/response schemas for clinical resources

These capabilities are intentionally deferred.

The current goal is to establish a clean backend foundation before exposing clinical use-cases.

---

## Planned API endpoints

The following endpoints are expected in later phases.

These are not implemented yet.

### Patient search

Planned endpoint:

    GET /patients?search={text}

Expected purpose:

Search patients by name, identifier, or other supported search text.

Related application use-case:

    SearchPatientsUseCase

---

### Patient summary

Planned endpoint:

    GET /patients/{patient_id}/summary

Expected purpose:

Return a structured clinical summary for a selected patient.

Related application use-case:

    GetPatientSummaryUseCase

---

### Observations by code

Planned endpoint:

    GET /patients/{patient_id}/observations?system={system}&code={code}

Expected purpose:

Return observations for a patient filtered by clinical code identity.

The code identity should be based on:

- `system`
- `code`

The display text should not be used as the identity of the clinical code.

Related application use-case:

    ListObservationsByCodeUseCase

---

### Patient bundle export

Planned endpoint:

    GET /patients/{patient_id}/bundle

Expected purpose:

Return a FHIR-like patient-centered export bundle.

Related application use-case:

    ExportPatientBundleUseCase

Important note:

The application layer currently returns a `PatientBundle` application model.

Final HTTP JSON serialization will be handled by the API/interface layer in a later phase.

---

### Audit events

Planned endpoint:

    GET /audit-events?limit={limit}

Expected purpose:

Return the most recent audit events for traceability review.

Related application use-case:

    ListAuditEventsUseCase

Initial expected behavior:

- default limit: 50
- maximum limit: 100
- ordered from newest to oldest

Advanced audit filtering and pagination are deferred.

---

## API design principles

The API should follow these principles as it evolves:

1. Keep routers thin.

   Routers should parse HTTP input, build value objects, call application use-cases, and map results to HTTP responses.

2. Do not put business logic in routers.

   Business orchestration belongs to the application layer.

3. Do not put persistence logic in routers.

   Database access belongs to infrastructure adapters.

4. Keep domain independent from HTTP.

   Domain entities and value objects must not import FastAPI, Pydantic, SQLAlchemy, or HTTP-specific types.

5. Keep application independent from HTTP.

   Application use-cases should not know about request objects, response objects, HTTP status codes, or FastAPI dependencies.

6. Preserve structured clinical evidence.

   API responses should preserve resource ids, dates, codes, quantities, references, and clinical structure.

7. Avoid premature broad repositories.

   Infrastructure adapters should implement the application ports already defined by the use-cases.

---

## Error handling

A standard API error response envelope has not been defined yet.

Future HTTP endpoints will need to map application errors such as:

- `ApplicationValidationError`
- `ApplicationNotFoundError`

to HTTP responses such as:

- `400 Bad Request`
- `404 Not Found`

This will be decided before exposing clinical use-cases through HTTP.

The `/health` endpoint does not currently require custom error handling.

---

## Versioning

Current API version:

    0.1.0

Current FastAPI app metadata:

    title: FHIR Mini-Gateway API
    version: 0.1.0

Formal API versioning strategy has not been introduced yet.

Possible future options include:

- URL versioning, such as `/v1/patients`
- header-based versioning
- no explicit versioning during the MVP phase

This decision is deferred until the public API surface grows.

---

## Security status

Authentication and authorization are not implemented yet.

Current `/health` endpoint is public.

Future clinical and audit endpoints should not be treated as public by default.

Authentication, RBAC, and audit trail enforcement belong to later phases.

---

## Synthetic data only

This project must only use synthetic/demo clinical data.

Do not use real patient data.

Do not commit real clinical identifiers, names, documents, or health records.

---

## Developer quick reference

From `apps/api`:

Install dependencies:

    pipenv install

Activate environment:

    pipenv shell

Run tests:

    pipenv run pytest

Run HTTP health tests:

    pipenv run pytest tests/unit/interfaces/http/test_health.py

Run API locally:

    pipenv run uvicorn fhir_gateway.interfaces.http.main:app --reload --app-dir src

Open health endpoint:

    http://127.0.0.1:8000/health

Open Swagger UI:

    http://127.0.0.1:8000/docs

Open ReDoc:

    http://127.0.0.1:8000/redoc
