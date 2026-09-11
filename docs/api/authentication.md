---
id: DOC-AUTH-HTTP-001
type: api-contract
status: active
implements:
  - TASK-002-14
spec_id: SPEC-002-AUTHENTICATION
---

# MyHub Authentication HTTP & Operator Contract

Status: V0.1 authentication contract for the Android-first, self-hosted MyHub instance.

This document describes the HTTP boundary currently implemented by `SPEC-002-AUTHENTICATION`. The canonical behavioral requirements remain the feature spec; this document is the client/operator contract for the implemented API.

## 1. Security model

Authentication is owned by each MyHub instance. Passkeys/WebAuthn are preferred, with an instance-local Argon2id password fallback. Successful authentication returns a high-entropy opaque bearer session whose reusable plaintext value is returned to the client only when the session is created. The server stores only a SHA-256 verifier for that bearer token.

Authentication establishes user identity. It does **not** grant family-resource access by itself. Membership status and backend capability checks remain authoritative for authorization.

The bootstrap token has one post-bootstrap purpose only: authorizing the exact initial Owner to establish the first real credential while the persisted initial-enrollment state is still open. It is never a general login credential and never directly creates an authenticated session.

## 2. Common conventions

Base API prefix:

```text
/api/v1/auth
```

JSON is used for request and response bodies unless otherwise documented.

A normal authenticated request uses:

```http
Authorization: Bearer <opaque-session-token>
```

The bearer token is secret material. Clients MUST NOT log it, put it in URLs, analytics events, crash metadata or application-visible diagnostics.

Initial Owner enrollment uses the operator bootstrap secret only on the dedicated bridge endpoints:

```http
X-MyHub-Bootstrap-Token: <operator-bootstrap-token>
```

The bootstrap token MUST NOT be sent to normal login endpoints.

## 3. Error envelope

Authentication-domain errors use the common request-ID-aware envelope:

```json
{
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "invalid credentials",
    "request_id": "<request-id>"
  }
}
```

Clients SHOULD branch on `error.code`, not human-readable `message`.

Current authentication error classes:

| Code | HTTP | Meaning |
|---|---:|---|
| `AUTH_INVALID_CREDENTIALS` | 401 | Invalid/revoked/expired credential, invalid session, invalid WebAuthn response, challenge problem or equivalent generic authentication failure. |
| `AUTH_INITIAL_ENROLLMENT_UNAUTHORIZED` | 401 | Initial Owner bridge authorization failed. |
| `AUTH_INITIAL_ENROLLMENT_CLOSED` | 409 | Initial Owner credential enrollment has already completed and the bootstrap bridge is permanently closed. |
| `AUTH_CREDENTIAL_CONFLICT` | 409 | Credential state conflicts with an existing credential, such as a unique login-name/credential collision. |
| `AUTH_UNAVAILABLE` | 409 | Instance state/configuration does not currently permit authentication. |
| `AUTH_THROTTLED` | 429 | Login abuse-control threshold is currently blocking the scope. |

Framework validation failures remain HTTP `422`. Unexpected server failures use the generic internal-error envelope and MUST NOT expose passwords, challenges, bearer tokens, private keys or provider internals.

## 4. Initial Owner passkey enrollment

### `POST /api/v1/auth/initial-owner/passkey/options`

Starts the one-time initial Owner passkey registration ceremony.

Required header:

```http
X-MyHub-Bootstrap-Token: <bootstrap-token>
```

Request body: none.

Success `200`:

```json
{
  "challenge_token": "<opaque-challenge-token>",
  "public_key": {
    "rp": {},
    "user": {},
    "challenge": "..."
  }
}
```

`public_key` is the WebAuthn registration-options object consumed by the Android credential-provider integration. The exact shape is provider/WebAuthn data and should be forwarded without weakening RP ID, origin or user-verification requirements.

The challenge is short-lived and single-use. Requesting options does not authenticate the Owner and does not close initial enrollment.

### `POST /api/v1/auth/initial-owner/passkey/verify`

Verifies the Android/WebAuthn registration response, persists the public credential, permanently closes the initial-enrollment bridge and returns the first normal MyHub session.

Required header:

```http
X-MyHub-Bootstrap-Token: <bootstrap-token>
```

Request:

```json
{
  "challenge_token": "<token-returned-by-options>",
  "credential": {
    "id": "...",
    "rawId": "...",
    "type": "public-key",
    "response": {}
  }
}
```

Success `200`:

```json
{
  "user_id": "<uuid>",
  "session_id": "<uuid>",
  "bearer_token": "<opaque-secret>",
  "expires_at": "<ISO-8601 timestamp>"
}
```

Critical invariants:

- only the exact initial Owner created by SPEC-001 is eligible;
- RP ID is derived from the canonical instance host;
- expected origin is derived from the canonical instance URL;
- user verification is required;
- a valid challenge is consumed in its own committed boundary before downstream credential verification, so a failed verification cannot make it replayable;
- the server stores only public passkey material;
- successful enrollment sets persisted initial-enrollment state to complete;
- the same bootstrap bridge cannot be used again afterward.

## 5. Initial Owner password enrollment

### `POST /api/v1/auth/initial-owner/password`

Alternative initial Owner enrollment when a passkey cannot or will not be used initially.

Required header:

```http
X-MyHub-Bootstrap-Token: <bootstrap-token>
```

Request:

```json
{
  "login_name": "owner",
  "password": "<secret>"
}
```

Success `200` returns the same `SessionResponse` as passkey verification.

`login_name` is instance-local and normalized using Unicode NFKC, trim and case-folding rules. Display name is never treated as the login identifier.

Password storage uses Argon2id. Plaintext passwords are never persisted and must not be logged.

Successful enrollment permanently closes the initial Owner bootstrap bridge just like successful passkey enrollment.

## 6. Returning-user passkey authentication

### `POST /api/v1/auth/passkey/options`

Starts a usernameless passkey authentication ceremony.

Request body: none.

Success `200`:

```json
{
  "challenge_token": "<opaque-challenge-token>",
  "public_key": {}
}
```

The server creates a short-lived authentication challenge and requires user verification. The endpoint is subject to the IP-scoped login throttle.

### `POST /api/v1/auth/passkey/verify`

Request:

```json
{
  "challenge_token": "<token-returned-by-options>",
  "credential": {
    "id": "<base64url credential id>",
    "type": "public-key",
    "response": {}
  }
}
```

Success `200` returns `SessionResponse`.

Server verification includes:

- single-use challenge validation;
- expected RP ID;
- expected origin;
- required user verification;
- lookup of the stored non-revoked credential by credential ID;
- `userHandle` binding to the stored MyHub user when `userHandle` is present;
- stored public-key verification;
- sign-count update;
- passkey backup-state consistency/update.

Unknown and revoked credentials collapse to the generic invalid-credentials response.

## 7. Password fallback login

### `POST /api/v1/auth/password/login`

Request:

```json
{
  "login_name": "owner",
  "password": "<secret>"
}
```

Success `200` returns `SessionResponse`.

Invalid login name and invalid password intentionally share `AUTH_INVALID_CREDENTIALS`; callers must not depend on account-enumeration details.

A successful login may transparently rehash the stored password when the configured Argon2id policy has become stronger.

Both normalized-login and client-IP abuse-control scopes apply. Failure counters are committed independently from the failed authentication transaction so an invalid attempt cannot erase its own throttle evidence.

## 8. Password enrollment for an authenticated user

### `POST /api/v1/auth/password/enroll`

Required header:

```http
Authorization: Bearer <opaque-session-token>
```

Request:

```json
{
  "login_name": "alan",
  "password": "<secret>"
}
```

Success:

```text
204 No Content
```

The authenticated session determines the target `user_id`. A caller cannot choose another user's ID in the payload.

The endpoint creates or replaces that user's password fallback and reactivates it if a prior password credential record had been revoked. Login-name uniqueness remains instance-wide after normalization.

## 9. Logout

### `POST /api/v1/auth/logout`

Required header:

```http
Authorization: Bearer <opaque-session-token>
```

Success:

```text
204 No Content
```

Logout revokes the presented server session. Revocation is backend-authoritative and does not depend on deleting frontend state.

## 10. Android Digital Asset Links

### `GET /.well-known/assetlinks.json`

This endpoint is intentionally outside `/api/v1` because Android resolves it from the instance origin.

Configured production response:

```json
[
  {
    "relation": ["delegate_permission/common.get_login_creds"],
    "target": {
      "namespace": "android_app",
      "package_name": "<android-application-id>",
      "sha256_cert_fingerprints": [
        "AA:BB:..."
      ]
    }
  }
]
```

If Android package/certificate configuration is absent in development, the endpoint returns an empty association document instead of fabricating trust.

Operators MUST configure the signing-certificate SHA-256 fingerprint that actually signs the distributed Android build. Changing package/signing identity or the canonical host can invalidate passkey association and must be treated as an identity migration concern.

## 11. Challenge semantics

Challenge configuration:

```text
MYHUB_AUTH_CHALLENGE_TTL_SECONDS
```

Default: `300` seconds.
Allowed range: `30..900` seconds.

WebAuthn challenge requirements:

- 32 bytes from a cryptographically secure random generator;
- purpose-bound to registration or authentication;
- optionally bound to the expected user where the ceremony requires it;
- only SHA-256 verifier persisted;
- finite expiration;
- single use;
- row-locked consumption;
- valid challenge consumption committed before downstream WebAuthn verification.

Clients should treat any failed ceremony as requiring a new options/challenge request.

## 12. Session semantics

Session configuration:

```text
MYHUB_AUTH_SESSION_TTL_SECONDS
```

Default: `2592000` seconds (30 days).
Allowed range: `300` seconds through `31536000` seconds (365 days).

Properties:

- opaque random bearer token;
- server persists SHA-256 verifier, not reusable plaintext bearer;
- finite expiry;
- individual revocation;
- server-side revocation is authoritative;
- session identity and family authorization are separate concerns.

The Android client should place the bearer secret in platform-appropriate secure storage. Exact mobile secure-storage implementation is governed by the mobile architecture/security work and must not downgrade to plain AsyncStorage or logging.

## 13. Argon2id configuration

Environment variables:

```text
MYHUB_PASSWORD_ARGON2_MEMORY_KIB
MYHUB_PASSWORD_ARGON2_TIME_COST
MYHUB_PASSWORD_ARGON2_PARALLELISM
```

Current enforced minimums:

```text
memory:      19456 KiB
iterations:  2
parallelism: 1
```

Operators may raise these values. The configuration validator prevents lowering them below the project baseline.

Password input is secret material. Operators should assume application logs, reverse-proxy access logs and observability pipelines must never receive password bodies.

## 14. Login abuse-control configuration

Environment variables:

```text
MYHUB_AUTH_LOGIN_MAX_FAILURES
MYHUB_AUTH_LOGIN_WINDOW_SECONDS
MYHUB_AUTH_LOGIN_BLOCK_SECONDS
```

Defaults:

```text
max failures: 5
window:       300 seconds
block:        900 seconds
```

The V0.1 implementation deliberately uses PostgreSQL rather than Redis. Throttle keys are SHA-256 digests of opaque scopes such as client IP and normalized login name; raw throttle scope strings are not persisted in the throttle table.

Successful authentication clears the applicable throttle state. Failed authentication commits its throttle update even when the credential transaction itself rolls back.

This mechanism is a small-instance baseline, not an Internet-scale distributed rate-limiting service.

## 15. Operator environment checklist

A self-hosted instance using authentication should explicitly configure:

```text
MYHUB_DATABASE_URL
MYHUB_BOOTSTRAP_TOKEN
MYHUB_AUTH_CHALLENGE_TTL_SECONDS
MYHUB_AUTH_SESSION_TTL_SECONDS
MYHUB_PASSWORD_ARGON2_MEMORY_KIB
MYHUB_PASSWORD_ARGON2_TIME_COST
MYHUB_PASSWORD_ARGON2_PARALLELISM
MYHUB_AUTH_LOGIN_MAX_FAILURES
MYHUB_AUTH_LOGIN_WINDOW_SECONDS
MYHUB_AUTH_LOGIN_BLOCK_SECONDS
MYHUB_ANDROID_PACKAGE_NAME
MYHUB_ANDROID_SHA256_CERT_FINGERPRINTS
```

The canonical instance URL established by SPEC-001 is also an authentication invariant because its host becomes the WebAuthn RP ID and its origin becomes the expected WebAuthn origin.

Public/non-local canonical origins must use HTTPS.

## 16. Logging and observability rules

Never place the following in normal application logs, traces, metrics labels or error bodies:

- passwords;
- bootstrap token;
- session bearer token;
- raw WebAuthn challenge transport token;
- credential private-key material;
- server private identity key;
- complete authentication request bodies when they contain secret material.

Stable event/error codes and request IDs are preferred for correlation.

## 17. Android integration gate

The server-side contract does **not** close `TASK-002-15`.

Before MyHub freezes the production Android passkey implementation, the project still requires a real-device Credential Manager test using an Expo development build against a real/self-hosted-style HTTPS origin and its Digital Asset Links document.

Required evidence should include at minimum:

1. device model and Android version;
2. MyHub Android package/application ID;
3. signing-certificate fingerprint used for the test build;
4. HTTPS test instance origin;
5. successful Digital Asset Links association;
6. passkey creation result;
7. returning passkey authentication result;
8. behavior after app restart;
9. behavior when the credential provider is unavailable/cancelled;
10. captured failures without secret material.

Until that evidence exists, `TASK-002-15` remains **BLOCKED / needs physical-device evidence**, not completed by documentation or emulator assumptions.

## 18. Explicit non-goals of this contract

Not defined here:

- account/Owner recovery;
- social OAuth;
- browser cookie/CSRF profile;
- enterprise SSO;
- passkey federation between MyHub instances;
- hidden master credentials;
- permanent bootstrap bypass;
- Redis/distributed rate limiting;
- authorization capability mapping for family resources.

Those require their own specification/ADR when introduced.
