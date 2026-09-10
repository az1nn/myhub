---
id: PLAN-002-AUTHENTICATION
type: plan
status: active
depends_on:
  - SPEC-002-AUTHENTICATION
---

# Implementation Plan: Authentication

## Architecture

Keep authentication inside the FastAPI modular monolith under `modules/identity/` with explicit ports for WebAuthn verification, password hashing, challenge storage and session issuance.

Suggested shape:

```text
HTTP adapters
  -> AuthenticationService
      -> CredentialRepository
      -> ChallengeRepository
      -> WebAuthnProvider
      -> PasswordHasher
      -> SessionRepository
```

Authorization remains downstream and separate.

## Server WebAuthn implementation

Research baseline: evaluate/use the production-stable Python package `webauthn` maintained by Duo Labs rather than the similarly named `py-webauthn` package. At planning time, `webauthn` 3.0.0 is current and supports Python 3.10+.

The library is an implementation dependency, not a source of truth for MyHub policy. MyHub MUST explicitly supply/verify expected RP ID, origins, challenge and user-verification policy.

## RP ID and canonical instance URL

Derive the initial RP ID from the canonical instance hostname established by SPEC-001 and persist it as authentication configuration when credentials are first enrolled.

After first passkey enrollment, RP ID changes are prohibited through ordinary settings. A future domain-migration/recovery spec must handle such changes.

## Android Credential Manager spike

Before freezing the mobile adapter, create:

```text
docs/research/android-credential-manager-passkeys-spike.md
```

Validate on a real Android device/development build:

- React Native + Expo development-build compatibility;
- Credential Manager passkey creation;
- passkey authentication;
- arbitrary self-hosted HTTPS instance RP ID;
- `/.well-known/assetlinks.json` served by that instance;
- release and debug signing fingerprints;
- device/provider without an existing credential;
- canceled ceremony;
- offline/no-network behavior;
- invalid/unverified Digital Asset Links;
- reinstallation/new device behavior.

Do not select a long-term React Native wrapper solely from README claims; verify native behavior empirically.

## Digital Asset Links

Each instance serves `/.well-known/assetlinks.json` from operator-configured Android package/signing metadata. The association includes credential-sharing permission required by Android Credential Manager.

This is instance configuration because the same distributed Android app must authenticate against arbitrary family-owned instance domains.

## Initial Owner enrollment bridge

Add persisted state to the singleton instance/bootstrap record, conceptually:

```text
owner_enrollment_completed_at nullable
```

Flow:

```text
READY + initial Owner has no credential
  -> bootstrap token authorizes enrollment options only
  -> WebAuthn/passkey or password enrollment is verified
  -> credential persisted
  -> owner_enrollment_completed_at set atomically
  -> normal session issued
  -> bootstrap-authorized enrollment rejected forever after
```

The bootstrap token does not become a session token.

## Passkey credential model

Conceptual fields:

```text
id
user_id
credential_id
public_key
sign_count
transports
created_at
last_used_at
revoked_at
```

Persist additional WebAuthn metadata only when needed for verification/operations.

## Challenges

Persist server-side challenges with:

```text
id
ceremony_type
challenge_hash/value
user_id nullable
expires_at
consumed_at
created_at
```

Challenge consumption and credential verification must occur transactionally enough that one challenge cannot be accepted twice.

## Password fallback

Add an instance-local normalized `login_name` to authentication identity data rather than overloading mutable `display_name`.

Use Argon2id. Current OWASP baseline at planning time includes at least `m=19456 KiB, t=2, p=1`; implementation MAY select a stronger equivalent profile after measuring the target self-hosted hardware. Store algorithm/parameters in the encoded hash so work factors can evolve.

Password policy should favor length and password-manager compatibility over composition rules. Exact minimum/maximum lengths and breached-password checks belong to implementation/security checklist.

## Sessions

Use opaque high-entropy bearer session credentials for Android V0.x:

```text
client token = session_id.secret
server = session_id + hash/verifier(secret) + metadata
```

Properties:

- expiration required;
- revocation required;
- no plaintext secret at rest;
- last-used metadata may be tracked without storing request contents;
- token delivered only over TLS outside local development;
- client stores it in platform secure storage.

Exact default TTL is configuration and must be documented before implementation merge.

## Proposed API baseline

```text
POST /api/v1/auth/bootstrap-owner/passkeys/options
POST /api/v1/auth/bootstrap-owner/passkeys/verify
POST /api/v1/auth/bootstrap-owner/password

POST /api/v1/auth/passkeys/options
POST /api/v1/auth/passkeys/verify

POST /api/v1/auth/password
POST /api/v1/auth/logout
GET  /api/v1/auth/session

GET  /.well-known/assetlinks.json
```

Member credential enrollment after invitation will reuse identity primitives but is coordinated by SPEC-003 family membership/invitation flows.

## Abuse controls

Before production exposure add per-instance login throttling/backoff without introducing Redis solely for authentication. Persisted/database-backed counters or another simple single-instance mechanism are preferred until scale proves otherwise.

## Test plan

Server tests:

- registration challenge entropy/expiry/single-use;
- RP/origin mismatch rejection;
- credential registration verification;
- usernameless credential authentication;
- replay rejection;
- revoked credential rejection;
- Argon2id hashing and verification;
- login-name normalization/uniqueness;
- invalid password non-enumerating response;
- session creation/expiry/revocation;
- no plaintext session secret at rest;
- bootstrap Owner enrollment one-time gate;
- concurrent Owner enrollment;
- membership authorization remains separate.

Mobile spike tests are documented separately and must use real Android hardware/development builds for the critical Credential Manager path.

## Open decisions deliberately preserved

- account recovery;
- Owner recovery;
- final web/browser session/cookie model;
- exact React Native Credential Manager wrapper;
- domain migration after passkeys exist;
- social OAuth provider strategy.
