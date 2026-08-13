# Security Documentation

## Table of contents

* [1. Purpose](#1-purpose)
* [2. Current status](#2-current-status)
* [3. Security pipeline](#3-security-pipeline)
* [4. Authentication](#4-authentication)
* [5. JWT requirements](#5-jwt-requirements)
* [6. Token verification foundation](#6-token-verification-foundation)
* [7. Current principal](#7-current-principal)
* [8. Roles](#8-roles)
* [9. Permissions and RBAC](#9-permissions-and-rbac)
* [10. Authorization flow](#10-authorization-flow)
* [11. Public vs protected endpoints](#11-public-vs-protected-endpoints)
* [12. Demo token endpoint](#12-demo-token-endpoint)
* [13. Audit actor derivation](#13-audit-actor-derivation)
* [14. Security error behavior](#14-security-error-behavior)
* [15. Settings](#15-settings)
* [16. Testing strategy](#16-testing-strategy)
* [17. Security architecture and object lifecycles](#17-security-architecture-and-object-lifecycles)
* [18. MVP limitations](#18-mvp-limitations)
* [19. Post-MVP backlog references](#19-post-mvp-backlog-references)
* [20. UML documentation](#20-uml-documentation)
* [21. Related ADRs and documentation](#21-related-adrs-and-documentation)
* [22. Summary](#22-summary)

---

## 1. Purpose

This document explains the MVP security model for the `FHIR Gateway Viewer Lite` backend.

It documents how the project currently handles, or plans to handle during Phase 4 and Phase 5:

* authentication
* JWT verification
* current-principal extraction
* role-based access control
* permission checks
* public vs protected endpoints
* local/demo token issuing
* audit actor derivation
* security error behavior
* security-related settings
* architecture boundaries
* testing
* MVP limitations
* post-MVP hardening

This is living documentation.

The ADR records the architectural decision:

```text
docs/adr/0017-Phase_4-MVP SECURITY MODEL. Authentication, RBAC, and Audit Security Model.md
```

This README explains the operational model for maintainers and developers.

---

## 2. Current status

Current status:

```text
Phase 4 / Security foundation in progress
```

Completed:

* MVP security ADR
* standard API error envelope
* application/domain error mappings
* JWT settings
* HS256 verifier
* typed `VerifiedJwtClaims`
* project-owned token errors
* signature, issuer, audience, expiration, and claim validation
* HMAC secret length validation
* `CurrentPrincipal`
* application-scoped verifier composition
* Bearer credential extraction
* current-principal HTTP dependency
* `401 Unauthorized`
* `WWW-Authenticate: Bearer`
* verifier-configuration `500`
* authentication tests
* security framework boundary tests
* security documentation
* dependency-resolution and error-handling UML

Next:

```text
Phase 4 / Sub-issue F
RBAC permission model and authorization helpers
```

Pending in Phase 4:

* explicit role and permission primitives
* centralized role-to-permission mapping
* pure authorization helpers
* authorization-specific application error
* `403 Forbidden`
* trusted audit actor derivation
* audit write-side port/use-case foundation
* reusable security/audit dependency wiring
* final documentation and quality-gate update

Planned for Phase 5 or later:

* local/demo token endpoint
* protected clinical endpoints
* protected audit endpoint
* audit recording for selected operations
* frontend-facing demo authentication flow

Not part of the MVP:

* external OAuth/OIDC
* JWKS
* token revocation
* server-side auth sessions
* database users
* passwords
* registration
* patient-level consent policies

Current public endpoint:

```text
GET /health
```

No production clinical or audit endpoint exists yet.

---

## 3. Security pipeline

### 3.1. Current implemented flow

```text
HTTP request
    -> Authorization: Bearer <token>
        -> HTTPBearer(auto_error=False)
            -> JwtTokenVerifier
                -> VerifiedJwtClaims
                    -> CurrentPrincipal
```

The implemented pipeline stops at `CurrentPrincipal`.

### 3.2. Intended complete MVP flow

```text
HTTP request
    -> Bearer token
        -> JWT verification
            -> CurrentPrincipal
                -> role-to-permission mapping
                    -> permission check
                        -> protected use-case
                            -> trusted audit actor
```

### 3.3. Responsibility chain

```text
Raw JWT
    -> VerifiedJwtClaims
        -> CurrentPrincipal
            -> permissions/RBAC
```

Responsibilities:

```text
JwtTokenVerifier
    validates token cryptography and technical claims

VerifiedJwtClaims
    represents validated JWT-oriented data

CurrentPrincipal
    represents the trusted actor for one request

RBAC
    maps roles to permissions and decides access
```

### 3.4. Main concepts

| Concept | Meaning |
|---|---|
| Bearer token | Credential sent in the `Authorization` header |
| Raw JWT | Untrusted token string received from the client |
| Verified JWT claims | Claims returned after successful validation |
| CurrentPrincipal | Trusted runtime identity for one request |
| Role | Coarse-grained caller category |
| Permission | Fine-grained operation capability |
| RBAC | Mapping from roles to permissions |
| Audit actor | Trusted identity written to audit history |

### 3.5. Boundary rules

Token verification belongs to infrastructure/security because it depends on PyJWT.

`CurrentPrincipal` belongs to application/security.

HTTP extraction and exception-to-response translation belong to interfaces/http.

Pure authorization policy must remain testable without FastAPI.

Domain and application must not import:

* FastAPI
* PyJWT (`jwt`)
* SQLAlchemy

Domain and application must not return:

* HTTP responses
* HTTP status codes
* FastAPI exceptions
* JWT-library objects

---

## 4. Authentication

### 4.1. Bearer model

Protected endpoints use:

```text
Authorization: Bearer <token>
```

Example:

```http
GET /patients/pat-001/summary
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### 4.2. JWT-based MVP authentication

The token is not trusted merely because it contains claims.

The API first verifies:

* signature
* algorithm
* issuer
* audience
* expiration
* required claims
* claim shapes

Only then does it derive `CurrentPrincipal`.

### 4.3. Authentication result

Success:

```text
CurrentPrincipal
```

Failure:

```text
401 Unauthorized
```

Header:

```text
WWW-Authenticate: Bearer
```

Message:

```text
Authentication credentials are missing or invalid.
```

The response does not reveal the internal token failure.

### 4.4. Stateless requests

The API does not create a persistent server-side authentication session.

Each protected request sends its token.

```text
Request 1
    -> verify token
    -> build principal
    -> request ends

Request 2
    -> verify token again
    -> build a new principal
    -> request ends
```

### 4.5. HTTPBearer

The project uses:

```python
HTTPBearer(
    scheme_name="BearerAuth",
    bearerFormat="JWT",
    auto_error=False,
)
```

`HTTPBearer` extracts credentials.

It does not verify the JWT.

`auto_error=False` allows the project to use its own error envelope.

---

## 5. JWT requirements

### 5.1. Required claims

| Claim | Meaning |
|---|---|
| `iss` | Token issuer |
| `aud` | Intended API audience |
| `sub` | Stable caller identity |
| `exp` | Expiration timestamp |
| `iat` | Issued-at timestamp |
| `roles` | Roles assigned to caller |

### 5.2. Optional claims

| Claim | Meaning |
|---|---|
| `name` | Human-readable display name |
| `email` | Email address |

Optional claims are not required for authorization.

### 5.3. Signing strategy

Current MVP:

```text
HS256
```

The secret:

* comes from settings
* must not be hardcoded
* must be at least 32 bytes for the current verifier

### 5.4. Production-oriented evolution

Post-MVP:

* external OAuth2/OIDC
* asymmetric signing
* JWKS
* key rotation
* secrets management

---

## 6. Token verification foundation

Implementation status:

```text
Implemented
```

Location:

```text
apps/api/src/fhir_gateway/infrastructure/security/
```

Components:

```text
JwtTokenVerifier
VerifiedJwtClaims
TokenVerificationError
TokenVerifierConfigurationError
```

### 6.1. Responsibility

The verifier answers:

```text
Is this token authentic, valid, and usable?
```

It does not:

* perform login
* issue tokens
* create sessions
* check permissions
* know the endpoint
* return HTTP responses
* create audit events

### 6.2. Input and output

Input:

```text
raw JWT string
```

Success:

```text
VerifiedJwtClaims
```

Invalid credential:

```text
TokenVerificationError
```

Invalid server configuration:

```text
TokenVerifierConfigurationError
```

### 6.3. Verification flow

```text
JwtTokenVerifier.verify(token)
    -> validate token presence
    -> validate secret configuration
    -> validate minimum secret length
    -> decode using configured algorithm
    -> validate signature
    -> validate issuer
    -> validate audience
    -> validate expiration
    -> require core claims
    -> validate project-specific claim shapes
    -> return VerifiedJwtClaims
```

### 6.4. Project-specific shape validation

The verifier checks:

* `sub`, `iss`, and `aud` are non-empty strings
* `iat` and `exp` are integers and not booleans
* `roles` is a non-empty list or tuple
* every role is a non-empty string
* optional `name` and `email` are non-empty strings when present

### 6.5. VerifiedJwtClaims

Fields:

```text
subject
issuer
audience
issued_at
expires_at
roles
name
email
```

Example:

```text
VerifiedJwtClaims(
    subject="clinician-demo-001",
    issuer="fhir-gateway-local",
    audience="fhir-gateway-api",
    issued_at=1700000000,
    expires_at=1700003600,
    roles=("clinician",),
    name="Demo Clinician",
    email=None,
)
```

### 6.6. Invalid token vs bad configuration

```text
TokenVerificationError
    -> client credential problem
    -> 401 Unauthorized

TokenVerifierConfigurationError
    -> server configuration problem
    -> 500 Internal Server Error
```

The HTTP authentication dependency catches only `TokenVerificationError`.

---

## 7. Current principal

### 7.1. Definition

`CurrentPrincipal` is the trusted runtime identity for one authenticated request.

Fields:

```text
subject
roles
display_name
```

Example:

```text
CurrentPrincipal(
    subject="clinician-001",
    roles=("clinician",),
    display_name="Demo Clinician",
)
```

### 7.2. Claims vs principal

`VerifiedJwtClaims` answers:

```text
What did the verified JWT contain?
```

`CurrentPrincipal` answers:

```text
Who is the trusted actor for this request?
```

Transformation:

```text
claims.subject -> principal.subject
claims.roles   -> principal.roles
claims.name    -> principal.display_name
```

### 7.3. Invariants

* `subject` is a non-empty string
* `roles` is a non-empty tuple
* each role is a non-empty string
* `display_name` is `None` or a non-empty string
* the dataclass is immutable

### 7.4. Principal is not a patient

```text
Principal: clinician-001
Patient: pat-001
```

The principal is the actor.

The patient is the clinical subject.

### 7.5. Principal is not a database user

The MVP has no database-backed user account.

`CurrentPrincipal` comes from verified claims.

### 7.6. HTTP dependency

Location:

```text
apps/api/src/fhir_gateway/interfaces/http/dependencies/security.py
```

Responsibilities:

* extract Bearer credentials
* retrieve application-scoped verifier
* verify raw token
* build `CurrentPrincipal`
* map invalid credentials to `AuthenticationError`

It does not:

* map roles to permissions
* check authorization
* create audit events
* issue tokens
* access the database

### 7.7. Request lifecycle

Correct:

```text
request
    -> token verification
    -> CurrentPrincipal
    -> endpoint/dependencies use principal
    -> request ends
```

Incorrect:

```text
app.state.current_principal
```

A principal must never be shared between requests.

---

## 8. Roles

Initial MVP roles:

```text
clinician
auditor
admin
```

### 8.1. clinician

Expected permissions:

```text
patient:read
observation:read
condition:read
encounter:read
bundle:export
```

### 8.2. auditor

Expected permission:

```text
audit:read
```

An auditor does not automatically receive clinical permissions.

### 8.3. admin

Expected permissions:

```text
patient:read
observation:read
condition:read
encounter:read
bundle:export
audit:read
```

`admin` means full access only within the current MVP permission catalog.

It is not an unrestricted production superuser.

### 8.4. Unknown roles

Safe behavior:

```text
unknown role
    -> grants no permissions
```

A technically valid JWT with an unknown role is authenticated but not authorized for protected operations unless another recognized role grants the required permission.

Unknown roles must never imply administrator access.

---

## 9. Permissions and RBAC

Current implementation status:

```text
Planned for Phase 4 / Sub-issue F
```

Initial permissions:

```text
patient:read
observation:read
condition:read
encounter:read
bundle:export
audit:read
```

Initial mapping:

| Role | Permissions |
|---|---|
| `clinician` | `patient:read`, `observation:read`, `condition:read`, `encounter:read`, `bundle:export` |
| `auditor` | `audit:read` |
| `admin` | all six explicit MVP permissions |

Preferred authorization model:

```text
endpoint requires permission
principal has roles
roles map to permissions
policy checks permission
```

Routers must not scatter role checks such as:

```python
if "clinician" in principal.roles:
    ...
```

The RBAC policy should be:

* centralized
* explicit
* immutable where practical
* independently testable
* fail-closed for unknown roles

Planned pure operations:

```text
permissions_for_roles(...)
has_permission(...)
ensure_permission(...)
```

The future FastAPI dependency factory belongs to the later HTTP wiring step and should reuse the same pure policy.

---

## 10. Authorization flow

### 10.1. Authentication vs authorization

```text
Authentication:
    Who are you?

Authorization:
    Are you allowed to do this?
```

### 10.2. 401 Unauthorized

Use `401` when the API cannot establish a valid identity.

Examples:

* missing credentials
* wrong scheme
* malformed token
* invalid signature
* expired token
* wrong issuer
* wrong audience
* missing required claims
* invalid claim shapes

### 10.3. 403 Forbidden

Use `403` when identity is valid but permission is insufficient.

Example:

```text
principal roles:
    auditor

endpoint requires:
    patient:read

effective permissions:
    audit:read

result:
    403 Forbidden
```

### 10.4. Rule

```text
401 = no valid identity
403 = valid identity, insufficient permission
```

### 10.5. Intended dependency flow

```text
protected endpoint
    -> permission dependency
        -> get_current_principal()
            -> CurrentPrincipal
        -> resolve permissions
        -> check required permission
            -> continue
            or
            -> PermissionDeniedError
                -> 403 Forbidden
```

The pure policy is introduced before the reusable FastAPI permission dependency.

---

## 11. Public vs protected endpoints

### 11.1. Public

Current:

```text
GET /health
```

It does not access clinical or audit data.

### 11.2. Protected clinical endpoints

Planned:

```text
GET /patients
GET /patients/{patient_id}/summary
GET /patients/{patient_id}/observations
GET /patients/{patient_id}/bundle
```

They should require explicit permissions.

### 11.3. Protected audit endpoint

Planned:

```text
GET /audit-events
```

Expected permission:

```text
audit:read
```

### 11.4. No global authentication

Authentication is not applied globally because:

* `/health` remains public
* documentation routes may remain public during MVP development
* permissions vary by endpoint
* protection should be explicit and reviewable

---

## 12. Demo token endpoint

Planned for Phase 5:

```text
POST /auth/demo-token
```

Purpose:

* allow UI and integration tests to obtain a JWT
* avoid premature database users/passwords
* support local, test, development, and demo environments

Intended flow:

```text
UI
    -> POST /auth/demo-token
        -> JWT
            -> protected endpoint with Bearer token
```

Production boundary:

The endpoint must be disabled or rejected in production.

Token verification and token issuance are separate responsibilities.

---

## 13. Audit actor derivation

Current implementation status:

```text
Planned for later Phase 4 work
```

Trusted source:

```text
CurrentPrincipal.subject
```

Example:

```text
CurrentPrincipal.subject = "clinician-001"
AuditEvent.agent = "clinician-001"
```

A client must not submit an arbitrary trusted actor.

Bad:

```json
{
  "agent": "admin-001"
}
```

Correct:

```text
verified token
    -> CurrentPrincipal
        -> AuditEvent.agent
```

Future trusted non-human actors may include:

* system identity
* background job identity
* local/demo identity
* AI-assisted workflow identity

These must still be controlled runtime identities.

---

## 14. Security error behavior

Security errors use:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "field": null,
    "resource": null,
    "identifier": null
  }
}
```

### 14.1. Authentication error

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

### 14.2. Authorization error

Planned for Sub-issue F.

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

A `403` does not include a Bearer challenge.

### 14.3. Verifier configuration error

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

The real reason is logged internally.

### 14.4. Current mapping

```text
AuthenticationError             -> 401
TokenVerifierConfigurationError -> 500
```

Planned:

```text
PermissionDeniedError -> 403
```

### 14.5. General flow

```text
dependency / endpoint / use-case / domain / infrastructure
    -> raises exception
        -> FastAPI selects handler
            -> _build_error_response()
                -> ApiError
                    -> ApiErrorResponse
                        -> JSONResponse
```

---

## 15. Settings

Implemented:

| Setting | Environment variable | Default |
|---|---|---|
| `auth_jwt_secret` | `FHIR_GATEWAY_AUTH_JWT_SECRET` | `None` |
| `auth_jwt_issuer` | `FHIR_GATEWAY_AUTH_JWT_ISSUER` | `fhir-gateway-local` |
| `auth_jwt_audience` | `FHIR_GATEWAY_AUTH_JWT_AUDIENCE` | `fhir-gateway-api` |
| `auth_jwt_algorithm` | `FHIR_GATEWAY_AUTH_JWT_ALGORITHM` | `HS256` |

Rules:

* secrets are not committed
* `auth_jwt_secret` may be `None` at startup
* verification without a valid secret raises a server configuration error
* current HS256 secrets must be at least 32 bytes
* production secrets require a proper management strategy

Composition:

```text
Settings
    -> JwtTokenVerifier
        -> app.state.jwt_token_verifier
            -> get_current_principal()
```

The verifier is created at startup but verifies tokens only when a protected request requires it.

---

## 16. Testing strategy

### 16.1. Token-verifier tests

Cover:

* valid token
* missing/blank token
* missing secret
* short secret
* invalid signature
* expiration
* issuer
* audience
* required claims
* string claim shapes
* integer claim shapes
* roles shape
* optional claim shapes

### 16.2. CurrentPrincipal tests

Cover:

* valid principal
* missing display name
* immutability
* invalid subject
* invalid roles container
* empty roles
* invalid role values
* invalid display name

### 16.3. Authentication dependency tests

Cover:

* verifier retrieval
* valid Bearer JWT
* missing credentials
* wrong scheme
* malformed token
* invalid signature
* hidden internal token reason
* verifier configuration failure

A test-only protected route exercises dependency resolution.

No production route is added solely for testing.

### 16.4. Planned authorization tests

Sub-issue F should cover:

* clinician permissions
* auditor permissions
* explicit admin permissions
* multiple roles
* duplicate roles/permissions
* unknown roles
* immutable permission representation
* allowed permission
* denied permission
* `403` standard envelope
* no `WWW-Authenticate` on `403`
* distinction between `401` and `403`

### 16.5. Architecture boundary tests

Files:

```text
apps/api/tests/unit/architecture/test_persistence_boundaries.py
apps/api/tests/unit/architecture/test_security_boundaries.py
```

They protect domain/application from:

* SQLAlchemy
* FastAPI
* PyJWT's `jwt` namespace

Run:

```bash
pipenv run pytest tests/unit/architecture
```

### 16.6. Full quality gate

```bash
pipenv run ruff check src tests
pipenv run pytest
```

A documented green state must come from actual command execution.

---

## 17. Security architecture and object lifecycles

### 17.1. Application creation

```text
Uvicorn
    -> imports main.py
        -> app = create_app()
```

### 17.2. Application-scoped objects

```text
Settings
JwtTokenVerifier
SQLAlchemy engine
SQLAlchemy session factory
FastAPI application
```

The JWT verifier is safe to share because it contains configuration, not request credentials or a current user.

### 17.3. Request-scoped objects

```text
Request
HTTPAuthorizationCredentials
VerifiedJwtClaims
CurrentPrincipal
SQLAlchemy Session
adapters
use-cases
```

### 17.4. Lifecycle table

| Object | Lifecycle | Shared? |
|---|---|---|
| FastAPI app | Process lifetime | Yes, within one process |
| Settings | App lifetime | Yes |
| JwtTokenVerifier | App lifetime | Yes |
| Request | One HTTP call | No |
| Bearer credentials | One protected call | No |
| VerifiedJwtClaims | One authenticated call | No |
| CurrentPrincipal | One authenticated call | No |

### 17.5. Multiple workers

```text
Worker 1 -> app 1 -> verifier 1
Worker 2 -> app 2 -> verifier 2
```

Objects are not shared directly between operating-system processes.

### 17.6. Development reload

`--reload` may restart the process and create a new app and verifier.

---

## 18. MVP limitations

The MVP deliberately does not implement:

* external OAuth2/OIDC
* JWKS
* asymmetric signing
* key rotation
* refresh tokens
* revocation
* server-side auth sessions
* registration
* passwords
* database users
* fine-grained patient authorization
* consent rules
* break-glass
* production audit immutability
* real patient data
* production frontend authentication

JWT authentication alone does not make the project production-security complete.

---

## 19. Post-MVP backlog references

```text
BACKLOG / POST-MVP / HARDEN / Integrate external OAuth2/OIDC provider with JWKS validation
```

```text
BACKLOG / POST-MVP / HARDEN / Add token revocation and session management strategy
```

```text
BACKLOG / I2+ / EXPAND / Add fine-grained patient-level authorization and consent rules
```

```text
BACKLOG / POST-MVP / HARDEN / Add tamper-evident audit trail controls
```

```text
BACKLOG / I2+ / ARCH / Introduce policy engine for complex authorization rules
```

```text
BACKLOG / FUTURE-AI / AI-READY / Add security-aware audit context for future AI-assisted access
```

---

## 20. UML documentation

### 20.1. Dependency resolution

```text
docs/architecture/uml/api/http/dependencies-resolution/
├── annotated-depends-resolution-activity.puml
└── http-dependency-resolution-sequence.puml
```

These diagrams explain:

* route registration
* dependency graph construction
* request-time dependency resolution
* `Annotated[X, Depends(provider)]`
* request dependency caching
* SQLAlchemy session reuse
* `yield` cleanup
* current-principal resolution

### 20.2. Error handling

```text
docs/architecture/uml/api/http/error-handling/
├── http-error-handling-activity.puml
└── http-error-handling-sequence.puml
```

These diagrams explain:

* exception propagation
* handler selection
* standard error-envelope construction
* `401` authentication behavior
* verifier-configuration `500`
* application/domain error mapping

### 20.3. Living-documentation rule

Update UML when:

* `PermissionDeniedError` and `403` are implemented
* permission dependencies are added
* audit actor wiring is added
* production endpoints replace conceptual examples
* Phase 5 introduces request validation and endpoint-specific failures

The dependency UML should not show a FastAPI permission dependency before the sub-issue that actually introduces it.

---

## 21. Related ADRs and documentation

Security ADR:

```text
docs/adr/0017-Phase_4-MVP SECURITY MODEL. Authentication, RBAC, and Audit Security Model.md
```

HTTP composition ADR:

```text
docs/adr/0011-Phase_3-HTTP_API_structure_and_runtime_composition.md
```

Runtime settings ADR:

```text
docs/adr/0013-Phase_3-Settings__centralized_runtime_configuration.md
```

Audit persistence ADR:

```text
docs/adr/0015-Phase_3-Audit-event-persistence-strategy.md
```

API documentation:

```text
docs/api/README.md
```

Persistence documentation:

```text
docs/persistence/README.md
```

Roadmap:

```text
docs/roadmap.md
```

---

## 22. Summary

Current implemented security foundation:

```text
Authorization: Bearer <token>
    -> HTTPBearer(auto_error=False)
        -> JwtTokenVerifier.verify(token)
            -> VerifiedJwtClaims
                -> CurrentPrincipal
```

Next:

```text
CurrentPrincipal.roles
    -> explicit permissions
        -> centralized authorization policy
            -> allow
            or
            -> PermissionDeniedError
                -> 403 Forbidden
```

Key rule:

```text
Security decisions must be explicit, centralized, fail-closed, testable, and documented.
```
