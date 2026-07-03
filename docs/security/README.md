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
* [17. MVP limitations](#17-mvp-limitations)
* [18. Post-MVP backlog references](#18-post-mvp-backlog-references)
* [19. Related ADRs](#19-related-adrs)
* [20. Summary](#20-summary)

---

## 1. Purpose

This document explains the MVP security model for the `FHIR Gateway Viewer Lite` backend.

It documents how the project handles, or plans to handle during Phase 4 and Phase 5:

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
* error mapping foundation for validation, not-found, and internal errors
* JWT-related runtime settings
* infrastructure-level JWT token verifier
* typed `VerifiedJwtClaims`
* project-owned token verification errors
* local/MVP HS256 token verification foundation
* required JWT claim validation
* issuer validation
* audience validation
* expiration validation
* HMAC secret length validation
* roles shape validation
* token verification tests

The following security models are already defined but not fully wired through HTTP yet:

* Bearer-token-based authentication model
* JWT-based current-principal extraction model
* RBAC permission model
* trusted audit actor derivation model

The following security capabilities are planned during the remaining Phase 4 work:

* authentication HTTP dependency
* current-principal dependency
* RBAC authorization helpers
* reusable security dependencies for future protected endpoints
* audit actor derivation from trusted security context

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
* session management
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

## 3.1. High-level request flow

The intended MVP request flow is:

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

## 3.2. Token-to-authorization pipeline

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

The current principal is then used by authorization helpers.

## 3.3. Main concepts

| Concept             | Meaning                                                                      |
| ------------------- | ---------------------------------------------------------------------------- |
| Bearer token        | Credential sent by the client in the `Authorization` header                  |
| Raw JWT             | Token string received from the client; not trusted yet                       |
| Verified JWT claims | Claims extracted after signature, issuer, audience and expiration validation |
| CurrentPrincipal    | Trusted runtime identity derived from verified claims                        |
| Role                | Coarse-grained user category, such as `clinician` or `auditor`               |
| Permission          | Fine-grained operation capability, such as `patient:read`                    |
| RBAC                | Role-based access control; maps roles to permissions                         |
| Audit actor         | Trusted actor written to audit records                                       |

## 3.4. Boundary rule

Security translation to HTTP belongs to the HTTP/interface layer.

Token verification belongs to infrastructure/security because it depends on a JWT library.

Authorization decisions should be testable without a real HTTP server.

Domain and application layers must remain independent from FastAPI.

Domain and application layers must not directly return HTTP responses, status codes, or FastAPI exceptions.

---

## 4. Authentication

## 4.1. Bearer token model

Protected endpoints will use the HTTP `Authorization` header:

```text
Authorization: Bearer <token>
```

The token represents the caller's credentials.

Example:

```text
GET /patients/pat-001/summary
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## 4.2. JWT-based MVP authentication

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

## 4.3. Authentication result

A successful authentication process eventually produces a trusted `CurrentPrincipal`.

An unsuccessful authentication process returns:

```text
401 Unauthorized
```

using the standard API error response envelope.

HTTP authentication behavior is not wired yet.

That will be introduced by the current-principal HTTP dependency in the next security sub-issue.

---

## 5. JWT requirements

## 5.1. Required claims

The MVP JWT must include:

| Claim   | Meaning                                    |
| ------- | ------------------------------------------ |
| `iss`   | Issuer: who issued the token               |
| `aud`   | Audience: which API the token is meant for |
| `sub`   | Subject: stable identity of the caller     |
| `exp`   | Expiration time                            |
| `iat`   | Issued-at time                             |
| `roles` | Roles assigned to the caller               |

## 5.2. Optional claims

Optional claims may include:

| Claim   | Meaning                     |
| ------- | --------------------------- |
| `name`  | Human-readable display name |
| `email` | Email address               |

Optional claims must not be required for authorization decisions.

Authorization must rely on validated identity and roles/permissions.

## 5.3. MVP signing strategy

The MVP uses symmetric JWT signing.

Initial algorithm:

```text
HS256
```

The signing secret must come from environment-backed settings.

The signing secret must not be hardcoded in source code.

The current verifier rejects HMAC secrets shorter than 32 bytes.

## 5.4. Post-MVP signing strategy

A production-oriented implementation should move toward external OAuth2/OIDC provider integration with asymmetric signing and JWKS validation.

That is intentionally deferred to post-MVP backlog work.

---

## 6. Token verification foundation

Current implementation status: **implemented in infrastructure/security**.

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

## 6.1. Responsibility

The token verifier is responsible for answering:

```text
Is this token authentic, valid and usable?
```

The verifier does not:

* perform login
* create a user session
* check endpoint permissions
* know which endpoint is being accessed
* return HTTP responses
* raise FastAPI exceptions
* create audit events

It only verifies the token and returns trusted claims.

## 6.2. Expected verifier input and output

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

Output on bad verifier configuration:

```text
TokenVerifierConfigurationError
```

Conceptual example:

```text
JwtTokenVerifier.verify(token)
    -> validates configured secret
    -> validates HMAC secret length
    -> validates signature
    -> validates issuer
    -> validates audience
    -> validates expiration
    -> validates required claims
    -> validates roles shape
    -> returns VerifiedJwtClaims
```

## 6.3. What PyJWT validates

The verifier delegates JWT cryptographic and standard claim validation to PyJWT.

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

## 6.4. What the project validates after decode

After PyJWT successfully decodes the token, the project validates that the claims have a usable shape.

The verifier checks that:

* `sub` is a non-empty string
* `iss` is a non-empty string
* `aud` is a non-empty string
* `iat` is an integer
* `exp` is an integer
* `roles` is a non-empty list or tuple
* every role is a non-empty string
* `name`, when provided, is a non-empty string
* `email`, when provided, is a non-empty string

Reason:

A claim being present is not enough.

The API also needs claims to have a shape that the application can safely use.

## 6.5. VerifiedJwtClaims

`VerifiedJwtClaims` represents JWT claims after successful verification.

Conceptual fields:

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

It still contains JWT-oriented technical information such as issuer, audience, issued-at and expiration.

The next layer translates verified claims into the runtime actor model.

---

## 7. Current principal

## 7.1. Definition

`CurrentPrincipal` is the trusted runtime identity of the caller after successful authentication.

Conceptual fields:

```text
subject
display_name
roles
```

Example:

```text
CurrentPrincipal(
    subject="clinician-001",
    display_name="Demo Clinician",
    roles=("clinician",),
)
```

## 7.2. VerifiedJwtClaims vs CurrentPrincipal

`VerifiedJwtClaims` answers:

```text
What did the verified JWT contain?
```

`CurrentPrincipal` answers:

```text
Who is the trusted actor for this request?
```

Example transformation:

```text
VerifiedJwtClaims.subject -> CurrentPrincipal.subject
VerifiedJwtClaims.name    -> CurrentPrincipal.display_name
VerifiedJwtClaims.roles   -> CurrentPrincipal.roles
```

The application should not need to know about issuer, audience or JWT expiration after the principal has been established.

Those are token verification concerns.

## 7.3. Principal vs Patient

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

## 7.4. Principal vs database user

The MVP does not introduce database-backed users.

The principal is derived from a validated token.

Database-backed users, user registration, password login, and user lifecycle management are deferred.

---

## 8. Roles

## 8.1. Role list

The MVP defines these initial roles:

```text
clinician
auditor
admin
```

## 8.2. `clinician`

A `clinician` represents a clinical user allowed to read ordinary clinical data in the MVP.

Expected permissions:

```text
patient:read
observation:read
condition:read
encounter:read
bundle:export
```

## 8.3. `auditor`

An `auditor` represents a user allowed to inspect audit events.

Expected permissions:

```text
audit:read
```

An auditor does not automatically receive clinical read permissions.

## 8.4. `admin`

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

---

## 9. Permissions and RBAC

## 9.1. Permission list

Initial MVP permissions:

```text
patient:read
observation:read
condition:read
encounter:read
bundle:export
audit:read
```

## 9.2. Role-to-permission mapping

Initial mapping:

| Role        | Permissions                                                                                           |
| ----------- | ----------------------------------------------------------------------------------------------------- |
| `clinician` | `patient:read`, `observation:read`, `condition:read`, `encounter:read`, `bundle:export`               |
| `auditor`   | `audit:read`                                                                                          |
| `admin`     | `patient:read`, `observation:read`, `condition:read`, `encounter:read`, `bundle:export`, `audit:read` |

## 9.3. Permission checks

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

---

## 10. Authorization flow

## 10.1. Authentication vs authorization

Authentication answers:

```text
Who are you?
```

Authorization answers:

```text
Are you allowed to do this?
```

## 10.2. `401 Unauthorized`

Use `401 Unauthorized` when the API cannot establish a valid identity.

Examples:

* missing token
* malformed token
* invalid signature
* expired token
* wrong issuer
* wrong audience
* missing required claims

Meaning:

```text
The caller has not provided valid credentials.
```

## 10.3. `403 Forbidden`

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

## 10.4. Simple rule

```text
401 = no valid identity
403 = valid identity, insufficient permission
```

---

## 11. Public vs protected endpoints

## 11.1. Public endpoints

Current public endpoint:

```text
GET /health
```

The health endpoint is technical.

It does not expose clinical data, audit data, or application use-cases.

## 11.2. Protected clinical endpoints

Future clinical endpoints should require authentication and authorization by default.

Planned clinical endpoint groups include:

```text
GET /patients
GET /patients/{patient_id}/summary
GET /patients/{patient_id}/observations
GET /patients/{patient_id}/bundle
```

These endpoints should not be public by default.

## 11.3. Protected audit endpoints

Future audit endpoints should require authentication and authorization.

Planned audit endpoint group:

```text
GET /audit-events
```

Expected permission:

```text
audit:read
```

---

## 12. Demo token endpoint

## 12.1. Purpose

A local/demo token issuing endpoint is planned for Phase 5.

It allows the UI and integration tests to obtain a Bearer JWT without implementing:

* database-backed users
* password login
* user registration
* sessions
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
            -> calls protected endpoints with Authorization: Bearer <token>
```

## 12.2. Production boundary

The demo token endpoint must be limited to local/test/demo usage.

It must be disabled or rejected in production.

This endpoint is an MVP convenience, not production authentication.

## 12.3. Relationship to Phase 4

Phase 4 builds the security foundation:

```text
settings
token verification
current principal
RBAC
audit actor derivation
```

Phase 5 can use that foundation to expose a demo token endpoint and protected clinical endpoints.

The demo token endpoint is therefore not part of Sub-issue D.

Sub-issue D verifies tokens.

The demo token endpoint issues tokens.

Those are related but separate responsibilities.

---

## 13. Audit actor derivation

## 13.1. Trusted actor source

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

## 13.2. Request body must not define audit actor

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

## 13.3. Future actor sources

Future non-human actors may include:

* system identity
* background job identity
* local/demo identity
* AI-assisted workflow identity

Those must still be trusted runtime identities, not arbitrary request body values.

---

## 14. Security error behavior

## 14.1. Standard API error envelope

Security errors must use the standard API error response envelope:

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

## 14.2. Authentication error example

Status:

```text
401 Unauthorized
```

Body:

```json
{
  "error": {
    "code": "unauthorized",
    "message": "Authentication credentials were missing or invalid.",
    "field": null,
    "resource": null,
    "identifier": null
  }
}
```

## 14.3. Authorization error example

Status:

```text
403 Forbidden
```

Body:

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

## 14.4. Application and domain error relationship

The same API error envelope is also used for application/domain errors exposed through HTTP.

Examples:

```text
DomainValidationError      -> 400 Bad Request
ApplicationValidationError -> 400 Bad Request
ApplicationNotFoundError   -> 404 Not Found
Unexpected exception       -> 500 Internal Server Error
```

## 14.5. Current status

The standard API error envelope already exists.

Security-specific HTTP error mapping is not wired yet.

Token verification errors currently remain infrastructure errors.

The authentication HTTP dependency will later translate invalid/missing authentication into `401 Unauthorized`.

The authorization helper will later translate insufficient permissions into `403 Forbidden`.

---

## 15. Settings

## 15.1. Implemented security settings

The following Phase 4 security settings are implemented:

| Setting              | Environment variable              | Purpose                      |
| -------------------- | --------------------------------- | ---------------------------- |
| `auth_jwt_secret`    | `FHIR_GATEWAY_AUTH_JWT_SECRET`    | Local/MVP JWT signing secret |
| `auth_jwt_issuer`    | `FHIR_GATEWAY_AUTH_JWT_ISSUER`    | Expected token issuer        |
| `auth_jwt_audience`  | `FHIR_GATEWAY_AUTH_JWT_AUDIENCE`  | Expected token audience      |
| `auth_jwt_algorithm` | `FHIR_GATEWAY_AUTH_JWT_ALGORITHM` | Expected JWT algorithm       |

Current defaults:

```text
auth_jwt_secret    = None
auth_jwt_issuer    = "fhir-gateway-local"
auth_jwt_audience  = "fhir-gateway-api"
auth_jwt_algorithm = "HS256"
```

## 15.2. Secret handling rule

Secrets must not be committed to the repository.

The local/demo signing secret should be provided through environment-backed settings.

`auth_jwt_secret` intentionally defaults to `None` to avoid committing a usable signing secret to the repository.

The verifier requires a configured JWT secret before verifying tokens.

For HS256, the current verifier rejects secrets shorter than 32 bytes.

Production secrets should eventually come from a proper secrets management strategy.

## 15.3. Current implementation status

These security settings are implemented as part of Sub-issue D.

The verifier currently uses these settings conceptually, but HTTP dependency wiring has not been introduced yet.

That wiring belongs to the next security sub-issue.

---

## 16. Testing strategy

## 16.1. Token verification tests

Token verification tests currently cover:

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
* invalid `sub`, `iss`, and `aud` shape
* invalid `iat` and `exp` shape
* invalid `roles` shape
* empty roles
* invalid optional `name` and `email` shape
* missing optional `name` and `email`

Expected behavior:

```text
valid token   -> VerifiedJwtClaims
invalid token -> TokenVerificationError
bad config    -> TokenVerifierConfigurationError
```

## 16.2. Authentication tests

Authentication dependency tests should cover:

* missing `Authorization` header
* malformed `Authorization` header
* unsupported scheme
* invalid token
* valid token

Expected behavior:

```text
missing/invalid token -> 401 unauthorized
valid token           -> CurrentPrincipal
```

## 16.3. Authorization tests

Authorization tests should cover:

* principal has required permission
* principal lacks required permission
* unknown role
* multiple roles
* admin permissions

Expected behavior:

```text
missing permission -> 403 forbidden
allowed permission -> request continues
```

## 16.4. Audit actor tests

Audit actor tests should cover:

* audit actor comes from `CurrentPrincipal.subject`
* request body cannot override audit actor
* audit actor derivation is stable and explicit

## 16.5. Error envelope tests

Security errors should reuse the standard API error envelope.

Expected tests:

```text
401 -> {"error": {...}}
403 -> {"error": {...}}
```

---

## 17. MVP limitations

The MVP security model deliberately does not implement:

* external OAuth/OIDC provider integration
* JWKS validation
* asymmetric signing
* key rotation
* refresh tokens
* token revocation
* session management
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

---

## 18. Post-MVP backlog references

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

## 19. Related ADRs

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

## 20. Summary

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
```

The current project is still in Phase 4 security foundation work.

The API does not yet authenticate HTTP requests end-to-end.

The next security step is to translate:

```text
Authorization: Bearer <token>
    -> JwtTokenVerifier.verify(token)
        -> VerifiedJwtClaims
            -> CurrentPrincipal
```

Security features must not be documented as production-grade until the corresponding hardening backlog items are implemented.

The key rule is:

```text
Security decisions must be explicit, centralized, testable, and documented.
```
