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
* [21. Related ADRs](#21-related-adrs)
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
* demo/local token issuing
* audit actor derivation
* security error behavior
* security-related settings
* MVP limitations
* post-MVP security hardening

This document is living documentation.

The related ADR explains why the MVP security model was chosen.

This README explains how the current security model works, or is intended to work, from a maintainer/developer point of view.

Related ADR:

```text
docs/adr/0017-mvp-authentication-rbac-and-audit-security-model.md
```

---

## 2. Current status

Current security status: **Phase 4 / Security foundation in progress**

The following security-related work is already implemented:

* MVP security model ADR
* standard API error response envelope
* error mapping for validation, not-found, authentication, JWT verifier configuration, and unexpected internal errors
* JWT-related runtime settings
* infrastructure-level JWT token verifier
* typed `VerifiedJwtClaims`
* project-owned token verification errors
* local/MVP HS256 token-verification foundation
* required JWT claim validation
* issuer validation
* audience validation
* expiration validation
* HMAC secret length validation
* roles shape validation
* application-level `CurrentPrincipal`
* `CurrentPrincipal` invariant validation
* application-scoped JWT verifier composition
* HTTP Bearer credential extraction
* reusable current-principal HTTP dependency
* translation of invalid or missing credentials into `401 Unauthorized`
* `WWW-Authenticate: Bearer` response header
* safe handling of JWT verifier configuration errors as `500 Internal Server Error`
* token-verification tests
* current-principal tests
* authentication dependency tests
* security error-envelope tests

The following security capabilities are planned during the remaining Phase 4 work:

* role-to-permission mapping
* RBAC authorization helpers
* reusable permission dependencies for future protected endpoints
* `403 Forbidden` handling for insufficient permissions
* audit actor derivation from trusted security context
* security and audit dependency wiring for future endpoints
* final architecture-boundary verification
* final Phase 4 security documentation and quality-gate update

The following capabilities are planned for Phase 5 or later:

* demo/local token issuing endpoint
* protected clinical endpoints
* protected audit endpoints
* audit recording on selected patient access/export operations
* frontend-facing demo authentication flow

The following capabilities are not part of the MVP security foundation:

* external OAuth/OIDC integration
* JWKS validation
* token revocation
* server-side authentication session management
* database-backed users
* password login
* user registration
* patient-level consent/access control

Current public endpoint:

```text
GET /health
```

Clinical and audit endpoints are not currently exposed.

Future clinical and audit endpoints should not be treated as public by default.

---

## 3. Security pipeline

### 3.1. Current implemented authentication flow

The currently implemented authentication flow is:

```text
HTTP request
    -> Authorization: Bearer <token>
        -> HTTPBearer(auto_error=False)
            -> JwtTokenVerifier
                -> VerifiedJwtClaims
                    -> CurrentPrincipal
```

The pipeline currently stops after building `CurrentPrincipal`.

Authorization and audit wiring are still pending.

### 3.2. Complete intended MVP request flow

The complete intended MVP request flow is:

```text
HTTP request
    -> Authorization: Bearer <token>
        -> JWT verification
            -> CurrentPrincipal
                -> role-to-permission mapping
                    -> permission check
                        -> protected use-case
                            -> audit actor derived from principal
```

### 3.3. Token-to-authorization pipeline

The internal security pipeline should be understood as:

```text
Raw JWT
    -> VerifiedJwtClaims
        -> CurrentPrincipal
            -> Permissions/RBAC
```

Each step has a different responsibility.

```text
JwtTokenVerifier:
    Checks token cryptography and technical JWT claims.

VerifiedJwtClaims:
    Represents JWT claims after successful validation.

CurrentPrincipal:
    Represents the trusted actor for the current request.

RBAC:
    Translates roles into permissions and decides access.
```

This separation keeps the system understandable and testable.

The API must not jump directly from arbitrary token text to authorization decisions.

The token must first be verified.

The verified claims must then be translated into a current principal.

The current principal will later be used by authorization helpers.

### 3.4. Main concepts

| Concept             | Meaning                                                                              |
| ------------------- | ------------------------------------------------------------------------------------ |
| Bearer token        | Credential sent by the client in the `Authorization` header                          |
| Raw JWT             | Token string received from the client; not trusted yet                               |
| Verified JWT claims | Claims extracted after signature, issuer, audience, expiration, and shape validation |
| CurrentPrincipal    | Trusted runtime identity derived from verified claims                                |
| Role                | Coarse-grained user category, such as `clinician` or `auditor`                       |
| Permission          | Fine-grained operation capability, such as `patient:read`                            |
| RBAC                | Role-based access control; maps roles to permissions                                 |
| Audit actor         | Trusted actor written to audit records                                               |

### 3.5. Boundary rules

Security translation to HTTP belongs to the HTTP/interface layer.

Token verification belongs to infrastructure/security because it depends on a JWT library.

`CurrentPrincipal` belongs to application/security because it represents the authenticated actor required by application-level behavior.

Authorization decisions should remain testable without a real HTTP server.

Domain and application layers must remain independent from FastAPI.

Domain and application layers must remain independent from PyJWT.

Domain and application layers must not directly return:

* HTTP responses
* HTTP status codes
* FastAPI exceptions
* JWT-library objects

---

## 4. Authentication

### 4.1. Bearer token model

Protected endpoints use the HTTP `Authorization` header:

```text
Authorization: Bearer <token>
```

The token represents the caller's credentials.

Example:

```text
GET /patients/pat-001/summary
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### 4.2. JWT-based MVP authentication

The MVP authentication model uses signed JWTs.

A JWT acts as a signed digital credential.

The API validates the token before trusting any claims inside it.

The API must not trust a token only because it contains fields such as:

```json
{
  "sub": "admin-001",
  "roles": ["admin"]
}
```

The token must first pass verification.

### 4.3. Authentication result

A successful authentication process produces a trusted `CurrentPrincipal`.

Current implemented HTTP authentication flow:

```text
HTTP request
    -> Authorization: Bearer <token>
        -> HTTPBearer(auto_error=False)
            -> JwtTokenVerifier.verify(token)
                -> VerifiedJwtClaims
                    -> CurrentPrincipal
```

An unsuccessful authentication process returns:

```text
401 Unauthorized
```

using the standard API error response envelope.

The response includes:

```text
WWW-Authenticate: Bearer
```

The API intentionally returns a generic authentication error message.

It does not expose whether the token:

* was expired
* was malformed
* was signed with an invalid secret
* was issued by the wrong issuer
* targeted the wrong audience
* lacked required claims
* contained invalid claim shapes

### 4.4. Authentication does not create a server-side session

The current JWT model is stateless.

The API does not create or store a persistent authentication session for the user.

Each protected request must include its Bearer token.

Conceptually:

```text
Request 1
    -> sends JWT
    -> JWT is verified
    -> CurrentPrincipal is created
    -> request ends

Request 2
    -> sends JWT again
    -> JWT is verified again
    -> new CurrentPrincipal is created
    -> request ends
```

The API does not store the principal permanently between requests.

### 4.5. HTTPBearer responsibility

The HTTP dependency uses FastAPI `HTTPBearer` with:

```text
auto_error = False
```

Its responsibility is limited to extracting Bearer credentials.

It does not verify the JWT.

Conceptually:

```text
Authorization: Bearer abc123
    -> HTTPAuthorizationCredentials(
           scheme="Bearer",
           credentials="abc123"
       )
```

Using `auto_error=False` allows the project to preserve its own standard error envelope rather than returning FastAPI's default authentication error body.

---

## 5. JWT requirements

### 5.1. Required claims

The MVP JWT must include:

| Claim   | Meaning                                    |
| ------- | ------------------------------------------ |
| `iss`   | Issuer: who issued the token               |
| `aud`   | Audience: which API the token is meant for |
| `sub`   | Subject: stable identity of the caller     |
| `exp`   | Expiration time                            |
| `iat`   | Issued-at time                             |
| `roles` | Roles assigned to the caller               |

### 5.2. Optional claims

Optional claims may include:

| Claim   | Meaning                     |
| ------- | --------------------------- |
| `name`  | Human-readable display name |
| `email` | Email address               |

Optional claims must not be required for authorization decisions.

Authorization must rely on validated identity and roles/permissions.

### 5.3. MVP signing strategy

The MVP uses symmetric JWT signing.

Initial algorithm:

```text
HS256
```

The signing secret must come from environment-backed settings.

The signing secret must not be hardcoded in source code.

The current verifier rejects HMAC secrets shorter than 32 bytes.

### 5.4. Post-MVP signing strategy

A production-oriented implementation should move toward:

* external OAuth2/OIDC provider integration
* asymmetric signing
* JWKS validation
* key rotation
* production secrets management

That is intentionally deferred to post-MVP backlog work.

---

## 6. Token verification foundation

Current implementation status: **implemented in infrastructure/security**

The current implementation includes:

* `JwtTokenVerifier`
* `VerifiedJwtClaims`
* `TokenVerificationError`
* `TokenVerifierConfigurationError`
* required claim validation
* issuer validation
* audience validation
* expiration validation
* HMAC secret length validation
* roles shape validation

### 6.1. Responsibility

The token verifier is responsible for answering:

```text
Is this token authentic, valid and usable?
```

The verifier does not:

* perform login
* issue tokens
* create a user session
* check endpoint permissions
* know which endpoint is being accessed
* return HTTP responses
* raise FastAPI exceptions
* create audit events

It only verifies the token and returns trusted claims.

### 6.2. Expected verifier input and output

Input:

```text
raw JWT string
```

Output on success:

```text
VerifiedJwtClaims
```

Output on invalid token:

```text
TokenVerificationError
```

Output on invalid server configuration:

```text
TokenVerifierConfigurationError
```

Conceptual flow:

```text
JwtTokenVerifier.verify(token)
    -> validates configured secret
    -> validates HMAC secret length
    -> validates signature
    -> validates issuer
    -> validates audience
    -> validates expiration
    -> validates required claims
    -> validates claim shapes
    -> validates roles shape
    -> returns VerifiedJwtClaims
```

### 6.3. What PyJWT validates

The verifier delegates JWT cryptographic and standard-claim validation to PyJWT.

The verifier uses the configured values for:

```text
secret
algorithm
issuer
audience
```

and requires the expected claims:

```text
iss
aud
sub
exp
iat
roles
```

Conceptually:

```text
jwt.decode(
    token,
    expected_secret,
    algorithms=[expected_algorithm],
    issuer=expected_issuer,
    audience=expected_audience,
    required_claims=[iss, aud, sub, exp, iat, roles],
)
```

This means:

```text
token.payload.iss must match the expected issuer
token.payload.aud must match the expected audience
token.payload.exp must not be expired
token.payload must contain all required claims
token signature must match the expected secret and algorithm
```

### 6.4. What the project validates after decode

After PyJWT successfully decodes the token, the project validates that the claims have a usable shape.

The verifier checks that:

* `sub` is a non-empty string
* `iss` is a non-empty string
* `aud` is a non-empty string
* `iat` is an integer and not a boolean
* `exp` is an integer and not a boolean
* `roles` is a non-empty list or tuple
* every role is a non-empty string
* `name`, when provided, is a non-empty string
* `email`, when provided, is a non-empty string

Reason:

A claim being present is not enough.

The API also needs claims to have a shape that later layers can safely use.

### 6.5. VerifiedJwtClaims

`VerifiedJwtClaims` represents JWT claims after successful verification.

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
    issued_at=123456,
    expires_at=123999,
    roles=("clinician",),
    name="Demo Clinician",
    email=None,
)
```

This object is intentionally not the same as `CurrentPrincipal`.

It still contains JWT-oriented technical information such as:

* issuer
* audience
* issued-at time
* expiration time

The HTTP composition layer translates verified claims into the runtime actor model.

### 6.6. Invalid token vs invalid verifier configuration

The verifier distinguishes between two categories.

Invalid client credential:

```text
TokenVerificationError
```

Examples:

* invalid signature
* expired token
* wrong issuer
* wrong audience
* missing claim
* invalid claim shape

Invalid server configuration:

```text
TokenVerifierConfigurationError
```

Examples:

* missing JWT secret
* JWT secret shorter than 32 bytes

This distinction must remain visible to the HTTP layer:

```text
TokenVerificationError
    -> 401 Unauthorized

TokenVerifierConfigurationError
    -> 500 Internal Server Error
```

---

## 7. Current principal

### 7.1. Definition

`CurrentPrincipal` is the trusted runtime identity of the caller after successful authentication.

Current fields:

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

### 7.2. VerifiedJwtClaims vs CurrentPrincipal

`VerifiedJwtClaims` answers:

```text
What did the verified JWT contain?
```

`CurrentPrincipal` answers:

```text
Who is the trusted actor for this request?
```

Current transformation:

```text
VerifiedJwtClaims.subject
    -> CurrentPrincipal.subject

VerifiedJwtClaims.roles
    -> CurrentPrincipal.roles

VerifiedJwtClaims.name
    -> CurrentPrincipal.display_name
```

The application does not need to know about issuer, audience, JWT expiration, or PyJWT after the principal has been established.

Those are token-verification concerns.

### 7.3. CurrentPrincipal invariants

`CurrentPrincipal` validates its basic invariants.

Rules:

* `subject` must be a non-empty string
* `roles` must be a non-empty tuple
* every role must be a non-empty string
* `display_name` must be `None` or a non-empty string

The principal is immutable.

Its identity and roles must not change accidentally during a request.

### 7.4. Principal vs patient

A principal is not a patient.

A principal is the actor using the system.

A patient is the clinical subject whose data may be read.

Example:

```text
Principal: clinician-001
Patient: pat-001
```

The clinician may read the patient's data if authorization allows it.

The two concepts must remain separate.

### 7.5. Principal vs database user

The MVP does not introduce database-backed users.

The principal is derived from a validated token.

Database-backed users, user registration, password login, and user lifecycle management are deferred.

### 7.6. Current HTTP dependency

The current-principal HTTP dependency is implemented in:

```text
apps/api/src/fhir_gateway/interfaces/http/dependencies/security.py
```

Its responsibility is to:

* extract Bearer credentials from the HTTP request
* retrieve the configured `JwtTokenVerifier` from `app.state`
* verify the raw JWT
* translate `VerifiedJwtClaims` into `CurrentPrincipal`
* translate invalid or missing credentials into `AuthenticationError`

The dependency does not:

* check permissions
* map roles to permissions
* create audit events
* issue tokens
* create user sessions
* access the database

Conceptual flow:

```text
get_current_principal()
    -> HTTPBearer(auto_error=False)
    -> get_jwt_token_verifier(request)
    -> JwtTokenVerifier.verify(raw_token)
    -> CurrentPrincipal
```

`TokenVerificationError` is translated to `AuthenticationError`.

`TokenVerifierConfigurationError` is not translated to `AuthenticationError`, because invalid verifier configuration is a server problem, not a client-credential problem.

### 7.7. Request-scoped lifecycle

A new `CurrentPrincipal` is built for each successfully authenticated request.

It is not stored in `app.state`.

Correct lifecycle:

```text
Request starts
    -> token is verified
    -> CurrentPrincipal is created
    -> endpoint and dependencies use principal
    -> request ends
    -> principal is released
```

Incorrect design:

```text
app.state.current_principal
```

That would incorrectly mix identities between concurrent users and requests.

---

## 8. Roles

### 8.1. Role list

The MVP defines these initial roles:

```text
clinician
auditor
admin
```

### 8.2. `clinician`

A `clinician` represents a clinical user allowed to read ordinary clinical data in the MVP.

Expected permissions:

```text
patient:read
observation:read
condition:read
encounter:read
bundle:export
```

### 8.3. `auditor`

An `auditor` represents a user allowed to inspect audit events.

Expected permission:

```text
audit:read
```

An auditor does not automatically receive clinical read permissions.

### 8.4. `admin`

An `admin` represents a broad MVP administrator.

Expected permissions:

```text
patient:read
observation:read
condition:read
encounter:read
bundle:export
audit:read
```

In this MVP, `admin` means full read access to the defined MVP operations.

It does not represent unrestricted production superuser behavior.

### 8.5. Unknown roles

The behavior for unknown roles will be defined during RBAC implementation.

The recommended safe behavior is:

```text
unknown role
    -> grants no permissions
```

An unknown role must not be interpreted as administrator access.

---

## 9. Permissions and RBAC

Current implementation status: **planned for the next Phase 4 security sub-issue**

### 9.1. Permission list

Initial MVP permissions:

```text
patient:read
observation:read
condition:read
encounter:read
bundle:export
audit:read
```

### 9.2. Role-to-permission mapping

Initial mapping:

| Role        | Permissions                                                                                           |
| ----------- | ----------------------------------------------------------------------------------------------------- |
| `clinician` | `patient:read`, `observation:read`, `condition:read`, `encounter:read`, `bundle:export`               |
| `auditor`   | `audit:read`                                                                                          |
| `admin`     | `patient:read`, `observation:read`, `condition:read`, `encounter:read`, `bundle:export`, `audit:read` |

### 9.3. Permission checks

Endpoints should require permissions, not raw roles.

Preferred model:

```text
endpoint requires permission
principal has roles
roles map to permissions
permission check decides access
```

Example:

```text
GET /patients/{patient_id}/summary
    -> requires patient:read
```

A router should not scatter checks such as:

```text
if "clinician" in principal.roles
```

Instead, it should rely on centralized authorization helpers.

### 9.4. Current status

The principal already carries validated roles.

The following pieces do not exist yet:

* role-to-permission mapping implementation
* permission resolution
* reusable permission dependency
* authorization-specific exception
* `403 Forbidden` handler
* protected production endpoints

---

## 10. Authorization flow

### 10.1. Authentication vs authorization

Authentication answers:

```text
Who are you?
```

Authorization answers:

```text
Are you allowed to do this?
```

### 10.2. `401 Unauthorized`

Use `401 Unauthorized` when the API cannot establish a valid identity.

Examples:

* missing token
* unsupported authentication scheme
* malformed token
* invalid signature
* expired token
* wrong issuer
* wrong audience
* missing required claims
* invalid claim shapes

Meaning:

```text
The caller has not provided valid credentials.
```

This behavior is implemented.

### 10.3. `403 Forbidden`

Use `403 Forbidden` when the API knows who the caller is but the caller lacks permission.

Example:

```text
auditor-001 tries to read GET /patients/pat-001/summary
```

If the endpoint requires:

```text
patient:read
```

but the principal only has:

```text
audit:read
```

then the API should return:

```text
403 Forbidden
```

This behavior is not implemented yet.

### 10.4. Simple rule

```text
401 = no valid identity
403 = valid identity, insufficient permission
```

### 10.5. Intended authorization dependency flow

The intended flow is:

```text
protected endpoint
    -> permission dependency
        -> get_current_principal()
            -> CurrentPrincipal
        -> resolve principal permissions
        -> check required permission
            -> allow request
            or
            -> 403 Forbidden
```

---

## 11. Public vs protected endpoints

### 11.1. Public endpoints

Current public endpoint:

```text
GET /health
```

The health endpoint is technical.

It does not expose:

* clinical data
* audit data
* application use-cases
* database contents

It does not execute the current-principal dependency.

### 11.2. Protected clinical endpoints

Future clinical endpoints should require authentication and authorization by default.

Planned clinical endpoint groups include:

```text
GET /patients
GET /patients/{patient_id}/summary
GET /patients/{patient_id}/observations
GET /patients/{patient_id}/bundle
```

These endpoints should not be public by default.

### 11.3. Protected audit endpoints

Future audit endpoints should require authentication and authorization.

Planned audit endpoint group:

```text
GET /audit-events
```

Expected permission:

```text
audit:read
```

### 11.4. Authentication is not applied globally

The current security dependency is reusable but is not applied globally to the FastAPI application.

Reason:

* `/health` must remain public
* documentation routes may remain public during the MVP
* each protected operation should declare its security requirement explicitly
* future permission dependencies will differ by endpoint

---

## 12. Demo token endpoint

### 12.1. Purpose

A local/demo token-issuing endpoint is planned for Phase 5.

It allows the UI and integration tests to obtain a Bearer JWT without implementing:

* database-backed users
* password login
* user registration
* server-side sessions
* refresh tokens
* external OAuth/OIDC
* a production identity provider

Intended endpoint:

```text
POST /auth/demo-token
```

Intended flow:

```text
UI
    -> POST /auth/demo-token
        -> receives demo JWT
            -> calls protected endpoints
               with Authorization: Bearer <token>
```

### 12.2. Production boundary

The demo token endpoint must be limited to:

* local
* test
* demo/development usage

It must be disabled or rejected in production.

This endpoint is an MVP convenience, not production authentication.

### 12.3. Relationship to Phase 4

Phase 4 builds the security foundation:

```text
settings
token verification
current principal
RBAC
audit actor derivation
```

Phase 5 can use that foundation to expose:

* demo token endpoint
* protected clinical endpoints
* protected audit endpoints

Token verification and token issuance are separate responsibilities.

---

## 13. Audit actor derivation

Current implementation status: **planned for later Phase 4 security work**

### 13.1. Trusted actor source

Future audit event creation must derive the audit actor from trusted runtime context.

Preferred source:

```text
CurrentPrincipal.subject
```

Example:

```text
CurrentPrincipal.subject = "clinician-001"
AuditEvent.agent = "clinician-001"
```

### 13.2. Request body must not define audit actor

Request bodies must not be allowed to define the audit actor.

Bad model:

```json
{
  "action": "read",
  "agent": "admin-001"
}
```

The client could lie.

Correct model:

```text
validated token
    -> VerifiedJwtClaims
        -> CurrentPrincipal
            -> AuditEvent.agent
```

### 13.3. Future actor sources

Future non-human actors may include:

* system identity
* background job identity
* local/demo identity
* AI-assisted workflow identity

Those must still be trusted runtime identities, not arbitrary request-body values.

### 13.4. Current limitation

`CurrentPrincipal` exists, but no production audit write-side dependency currently consumes it.

Audit actor wiring will be introduced in a later Phase 4 sub-issue.

---

## 14. Security error behavior

### 14.1. Standard API error envelope

Security errors use the standard API error response envelope:

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

The API error envelope is defined in the HTTP/interface layer.

### 14.2. Authentication error example

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

This response is used for missing or invalid authentication credentials.

The response deliberately does not reveal the detailed token-verification failure.

### 14.3. Authorization error example

Current implementation status: **planned**

Expected status:

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

### 14.4. JWT verifier configuration error

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

The real internal reason is logged.

The client must not receive details such as:

```text
JWT secret is not configured.
JWT secret must be at least 32 bytes long.
```

### 14.5. Current security-related mappings

Current mappings:

```text
AuthenticationError             -> 401 Unauthorized
TokenVerifierConfigurationError -> 500 Internal Server Error
```

`TokenVerificationError` is translated by the HTTP authentication dependency into `AuthenticationError`.

`TokenVerifierConfigurationError` is not translated into `AuthenticationError`.

Reason:

```text
TokenVerificationError:
    the client credentials are invalid
    -> 401 Unauthorized

TokenVerifierConfigurationError:
    the server is misconfigured
    -> 500 Internal Server Error
```

Authorization-specific `403 Forbidden` mapping is not implemented yet.

### 14.6. Relationship with application and domain errors

The same API error envelope is used for application/domain errors exposed through HTTP.

Current mappings:

```text
DomainValidationError           -> 400 Bad Request
ApplicationValidationError      -> 400 Bad Request
ApplicationNotFoundError        -> 404 Not Found
AuthenticationError             -> 401 Unauthorized
TokenVerifierConfigurationError -> 500 Internal Server Error
Unexpected Exception            -> 500 Internal Server Error
```

### 14.7. Error flow

Conceptual error flow:

```text
dependency / endpoint / use-case / domain / infrastructure
    -> raises exception
        -> exception propagates to FastAPI
            -> FastAPI selects registered handler
                -> handler calls _build_error_response()
                    -> ApiError
                        -> ApiErrorResponse
                            -> JSONResponse
                                -> client
```

Exception handlers are registered when the application starts.

They are not registered once per request.

---

## 15. Settings

### 15.1. Implemented security settings

The following Phase 4 security settings are implemented:

| Setting              | Environment variable              | Purpose                                       |
| -------------------- | --------------------------------- | --------------------------------------------- |
| `auth_jwt_secret`    | `FHIR_GATEWAY_AUTH_JWT_SECRET`    | Local/MVP JWT signing and verification secret |
| `auth_jwt_issuer`    | `FHIR_GATEWAY_AUTH_JWT_ISSUER`    | Expected token issuer                         |
| `auth_jwt_audience`  | `FHIR_GATEWAY_AUTH_JWT_AUDIENCE`  | Expected token audience                       |
| `auth_jwt_algorithm` | `FHIR_GATEWAY_AUTH_JWT_ALGORITHM` | Expected JWT algorithm                        |

Current defaults:

```text
auth_jwt_secret    = None
auth_jwt_issuer    = "fhir-gateway-local"
auth_jwt_audience  = "fhir-gateway-api"
auth_jwt_algorithm = "HS256"
```

### 15.2. Secret-handling rule

Secrets must not be committed to the repository.

The local/demo signing secret should be provided through environment-backed settings.

`auth_jwt_secret` intentionally defaults to `None` to avoid committing a usable signing secret.

The verifier requires a configured JWT secret before verifying tokens.

For HS256, the current verifier rejects secrets shorter than 32 bytes.

Production secrets should eventually come from a proper secrets-management strategy.

### 15.3. Current application composition

The FastAPI application creates a configured `JwtTokenVerifier` during application startup and stores it in:

```text
app.state.jwt_token_verifier
```

The HTTP security dependency retrieves this verifier from the current request application state.

Conceptual flow:

```text
Settings
    -> JwtTokenVerifier
        -> app.state.jwt_token_verifier
            -> get_current_principal()
```

The verifier does not validate a token during application startup.

Token verification occurs when a protected request provides a Bearer JWT.

### 15.4. Application startup with missing secret

The application can start when:

```text
auth_jwt_secret = None
```

Reason:

* `/health` remains public
* token verification is not performed during startup
* protected-request verification will identify invalid configuration

When a protected request reaches a verifier without a valid secret:

```text
TokenVerifierConfigurationError
    -> 500 Internal Server Error
```

This behavior keeps public technical endpoints available while still treating invalid security configuration as a server failure for protected operations.

---

## 16. Testing strategy

### 16.1. Token-verification tests

Token-verification tests cover:

* valid token
* missing token
* blank token
* missing configured secret
* too-short configured secret
* invalid signature
* expired token
* wrong issuer
* wrong audience
* missing required claim
* invalid `sub`, `iss`, and `aud` shapes
* invalid `iat` and `exp` shapes
* invalid `roles` shape
* empty roles
* invalid optional `name` and `email` shapes
* missing optional `name` and `email`

Expected behavior:

```text
valid token   -> VerifiedJwtClaims
invalid token -> TokenVerificationError
bad config    -> TokenVerifierConfigurationError
```

### 16.2. CurrentPrincipal tests

Current-principal tests cover:

* valid principal
* missing optional display name
* immutability
* invalid subject
* non-tuple roles
* empty roles
* invalid role values
* invalid display name

Expected behavior:

```text
valid identity data   -> CurrentPrincipal
invalid identity data -> ApplicationValidationError
```

### 16.3. Authentication dependency tests

Authentication dependency tests cover:

* retrieval of the application-scoped JWT verifier
* missing `Authorization` header
* unsupported authentication scheme
* invalid token
* token with invalid signature
* valid token
* construction of expected `CurrentPrincipal`
* JWT verifier configuration error

Expected behavior:

```text
missing/invalid token -> 401 unauthorized
valid token           -> CurrentPrincipal
bad verifier config   -> 500 internal_server_error
```

The tests use a test-only protected endpoint to exercise FastAPI dependency resolution without adding a production endpoint solely for authentication testing.

### 16.4. Authorization tests

Authorization tests should cover:

* principal has required permission
* principal lacks required permission
* unknown role
* multiple roles
* admin permissions
* repeated permissions
* immutable permission representation where applicable

Expected behavior:

```text
missing permission -> 403 forbidden
allowed permission -> request continues
```

These tests belong to the upcoming RBAC sub-issue.

### 16.5. Audit actor tests

Audit actor tests should cover:

* audit actor comes from `CurrentPrincipal.subject`
* request body cannot override audit actor
* audit actor derivation is stable and explicit
* system actors are distinguishable from human actors if introduced

### 16.6. Error-envelope tests

Security error tests currently verify:

```text
401 -> standard error envelope
401 -> WWW-Authenticate: Bearer
500 verifier configuration -> standard generic envelope
500 verifier configuration -> internal details are hidden
```

Expected future tests:

```text
403 -> standard error envelope
```

### 16.7. Architecture boundary tests

Architecture tests should guarantee that:

* domain does not import FastAPI
* application does not import FastAPI
* domain does not import PyJWT
* application does not import PyJWT
* domain does not import SQLAlchemy
* application does not import SQLAlchemy

---

## 17. Security architecture and object lifecycles

### 17.1. FastAPI application lifecycle

The FastAPI application is created when the server process starts.

Conceptually:

```text
Uvicorn
    -> imports main.py
        -> app = create_app()
```

The same application instance processes multiple requests.

It is not recreated for each endpoint call.

### 17.2. Application-scoped security objects

The following security object is application-scoped:

```text
JwtTokenVerifier
```

It is created during `create_app()` and stored in:

```text
app.state.jwt_token_verifier
```

It is safe to share because it:

* does not contain request credentials
* does not contain the current user
* stores only verifier configuration
* is effectively stateless between verifications

### 17.3. Request-scoped security objects

The following objects are request-scoped:

```text
HTTPAuthorizationCredentials
VerifiedJwtClaims
CurrentPrincipal
```

They belong only to one HTTP request.

They must not be stored globally or in `app.state`.

### 17.4. Object lifecycle table

| Object              | Lifecycle                   | Shared?                 |
| ------------------- | --------------------------- | ----------------------- |
| FastAPI application | Server-process lifetime     | Yes, within one process |
| Settings            | Application lifetime        | Yes                     |
| JwtTokenVerifier    | Application lifetime        | Yes                     |
| HTTP Request        | One HTTP call               | No                      |
| Bearer credentials  | One protected HTTP call     | No                      |
| VerifiedJwtClaims   | One authenticated HTTP call | No                      |
| CurrentPrincipal    | One authenticated HTTP call | No                      |

### 17.5. Multiple workers

If Uvicorn runs several worker processes:

```text
Worker 1 -> FastAPI app 1 -> JwtTokenVerifier 1
Worker 2 -> FastAPI app 2 -> JwtTokenVerifier 2
Worker 3 -> FastAPI app 3 -> JwtTokenVerifier 3
```

Each process owns its own application-scoped objects.

No application object is shared directly between operating-system processes.

### 17.6. Development reload

When Uvicorn runs with:

```text
--reload
```

a source-code change may restart the application process.

The old FastAPI application instance is discarded and a new one is created.

---

## 18. MVP limitations

The MVP security model deliberately does not implement:

* external OAuth/OIDC provider integration
* JWKS validation
* asymmetric signing
* key rotation
* refresh tokens
* token revocation
* server-side authentication session management
* user registration
* password login
* database-backed users
* fine-grained patient-level authorization
* consent rules
* break-glass access
* production-grade audit immutability
* real patient data
* production frontend authentication flow

These limitations are intentional.

The MVP goal is to create a clean, testable, extensible security foundation without over-building production identity infrastructure too early.

The existence of JWT authentication does not mean the project is production-security complete.

---

## 19. Post-MVP backlog references

Deferred security hardening and expansion items include:

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

### 20.1. Current Phase 4 diagrams

Current error-handling diagrams may be stored in:

```text
docs/architecture/uml/error-handling/
```

Suggested files:

```text
http-error-handling-sequence.puml
http-error-handling-activity.puml
```

### 20.2. Purpose

The sequence diagram explains:

```text
who calls whom
in what order
where an exception is raised
how it propagates
which handler is selected
how the JSON response is built
```

The activity diagram explains:

```text
which response is selected
for each exception type
```

### 20.3. Living-documentation rule

The current diagrams must be updated when Phase 4 introduces:

* authorization exception
* `403 Forbidden`
* permission dependencies
* audit actor wiring
* additional security-related error mappings

They must also be reviewed during Phase 5 when real endpoints introduce:

* path-parameter validation
* query-parameter validation
* request-body validation
* framework-generated `422` responses
* endpoint-specific not-found flows
* persistence failures
* audit recording flows

### 20.4. Definitive post-Phase 5 UML set

The definitive architecture and runtime-flow UML set should be created after Phase 5, when the first protected clinical and audit endpoints exist.

That set should be based on implemented code rather than speculative interactions.

---

## 21. Related ADRs

Security model:

```text
docs/adr/0017-mvp-authentication-rbac-and-audit-security-model.md
```

AuditEvent persistence strategy:

```text
docs/adr/0015-audit-event-persistence-strategy.md
```

HTTP API structure and runtime composition:

```text
docs/adr/0011-http-api-structure-and-runtime-composition.md
```

Centralized runtime configuration:

```text
docs/adr/0013-centralized-runtime-configuration.md
```

---

## 22. Summary

The MVP security model is intentionally simple:

```text
Raw JWT
    -> VerifiedJwtClaims
        -> CurrentPrincipal
            -> roles
                -> permissions/RBAC
                    -> protected endpoint
                        -> trusted audit actor
```

The currently implemented security foundation covers:

```text
JWT settings
    -> JwtTokenVerifier
        -> VerifiedJwtClaims
            -> CurrentPrincipal
```

The HTTP authentication dependency is implemented:

```text
Authorization: Bearer <token>
    -> HTTPBearer(auto_error=False)
        -> JwtTokenVerifier.verify(token)
            -> VerifiedJwtClaims
                -> CurrentPrincipal
```

The API can now authenticate a request through a reusable dependency, but production clinical and audit endpoints do not exist yet.

The next security step is RBAC authorization:

```text
CurrentPrincipal.roles
    -> permissions
        -> permission check
            -> allow request
            or
            -> 403 Forbidden
```

Security features must not be documented as production-grade until the corresponding hardening backlog items are implemented.

The key rule is:

```text
Security decisions must be explicit, centralized, testable, and documented.
```
