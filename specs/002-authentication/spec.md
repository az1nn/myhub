---
id: SPEC-002-AUTHENTICATION
type: spec
status: active
requires:
  - REQ-AUTH-001
  - REQ-AUTH-002
  - REQ-AUTH-003
  - REQ-AUTH-004
  - REQ-AUTH-005
  - REQ-AUTH-006
  - REQ-AUTH-007
  - REQ-AUTH-008
  - REQ-AUTH-009
  - REQ-AUTH-010
critical_requirements:
  - REQ-AUTH-001
  - REQ-AUTH-004
  - REQ-AUTH-005
  - REQ-AUTH-006
  - REQ-AUTH-007
  - REQ-AUTH-010
constrained_by:
  - ADR-007
  - ADR-010
  - ADR-011
  - ADR-012
  - ADR-013
  - ADR-015
  - ADR-018
  - ADR-019
depends_on:
  - SPEC-001-INSTANCE-BOOTSTRAP
---

# Feature Specification: Authentication

## Problem

Each self-hosted MyHub instance needs to authenticate family members without depending on a mandatory central identity provider. Authentication must support an Android-first passkey experience while retaining a secure password fallback and preserving backend-controlled authorization.

## Baseline

The approved architecture already establishes:

- authentication is owned by each MyHub instance;
- passkeys/WebAuthn are preferred;
- password is fallback;
- social OAuth may exist later but cannot be required;
- local biometrics/PIN may protect the mobile app but are not server authentication;
- authorization remains a separate backend responsibility.

## Requirements

### REQ-AUTH-001 — Instance-owned authentication

A READY MyHub instance MUST be capable of registering and authenticating users without Google Sign-In, Auth0, Cognito or another mandatory external IdP.

Credential providers used to store passkeys on a device are not MyHub identity authorities: the MyHub instance verifies and owns the server-side credential record.

### REQ-AUTH-002 — Passkey-first registration

The preferred credential enrollment path MUST be WebAuthn/passkey. The server MUST generate registration options/challenges and MUST verify the returned credential before persistence.

Passkeys SHOULD be discoverable credentials so normal login can be usernameless where the platform supports it.

### REQ-AUTH-003 — Password fallback

A user MUST be able to enroll a password fallback when passkeys are unavailable or intentionally not used.

Password fallback uses a dedicated instance-local `login_name`; `display_name` MUST NOT be treated as a unique or immutable login identifier.

`login_name` MUST be unique within the instance after normalization. Exact UX rules for choosing/changing it belong to the implementation plan.

### REQ-AUTH-004 — Verified challenge semantics

WebAuthn challenges MUST be cryptographically random, short-lived, single-use and bound to their ceremony (`registration` or `authentication`).

Verification MUST enforce the expected RP ID and accepted origins and MUST reject expired, replayed or mismatched challenges.

### REQ-AUTH-005 — Server-side sessions

Successful authentication MUST establish a server-recognized, expiring and revocable session. Authentication state MUST NOT depend solely on frontend state.

For the Android client, API authentication uses a high-entropy opaque bearer session credential stored only as a verifier/hash on the server. Exact lifetime is configuration, not infinite retention.

The future web-client cookie/CSRF profile remains outside this Android-first spec until web scope is closed.

### REQ-AUTH-006 — Password storage

Passwords MUST never be stored or reversibly encrypted. New password credentials MUST use Argon2id with parameters meeting or exceeding the current project security baseline. Per-password salts are mandatory through the password hashing implementation.

The work factor MUST be configurable so deployments can raise cost without schema changes.

### REQ-AUTH-007 — Initial Owner credential enrollment

SPEC-001 creates the initial Owner before SPEC-002 credentials exist. MyHub MUST provide one narrowly scoped bridge for that Owner to enroll the first passkey and/or password fallback.

The configured bootstrap token MAY authorize only this initial credential-enrollment ceremony while all of the following are true:

1. the instance is READY;
2. the target is the exact initial Owner created by SPEC-001;
3. that Owner has not completed initial credential enrollment;
4. the request is for credential enrollment only.

The bootstrap token MUST NOT create a general authenticated session by itself. Once initial Owner credential enrollment succeeds, this bootstrap-authorized enrollment path MUST be permanently disabled in persisted instance state.

### REQ-AUTH-008 — Credential and session revocation

The backend MUST support revoking an individual passkey/password credential where meaningful and revoking sessions independently. Revocation takes effect server-side without requiring a client release.

At least one usable authentication credential MUST remain unless an explicit future recovery/removal policy allows otherwise.

### REQ-AUTH-009 — Android self-hosted RP association

For Android passkeys, each self-hosted instance MUST be able to publish the Digital Asset Links association required for the MyHub Android package/signing certificate at the instance domain.

The WebAuthn RP ID is bound to the instance canonical host. Once passkeys exist, changing the canonical host/RP ID is a credential migration/recovery problem and MUST NOT be treated as an ordinary settings edit.

Exact React Native/Expo native-module integration MUST be validated in a dedicated Credential Manager spike before the mobile implementation is frozen.

### REQ-AUTH-010 — No insecure recovery shortcut

Account recovery and Owner recovery remain open product/security decisions. SPEC-002 MUST NOT introduce security questions, a hidden master password, permanent bootstrap bypass, email dependency, or any other undeclared recovery mechanism.

If all usable credentials are lost, the system MUST fail closed until an approved recovery design exists.

## User story — initial Owner enrollment

As the initial Owner who just bootstrapped an instance, I want to enroll a passkey so the bootstrap secret stops being useful for identity enrollment and normal authentication can begin.

Acceptance criteria:

- only the exact initial Owner can use the bootstrap-authorized enrollment path;
- a WebAuthn challenge is generated and verified;
- the public credential is persisted, never the private passkey key;
- successful enrollment permanently closes the bootstrap enrollment path;
- a normal server session is issued only after verified credential enrollment.

## User story — returning member with passkey

As a family member, I want to sign in with my passkey without typing a password.

Acceptance criteria:

- server-generated authentication challenge;
- Credential Manager/WebAuthn response verified against RP/origin/challenge;
- unknown/revoked credentials rejected;
- successful verification establishes a revocable session;
- replaying the same challenge fails.

## User story — password fallback

As a member whose passkey is unavailable, I want to sign in using my instance-local login name and password.

Acceptance criteria:

- password is verified against Argon2id hash;
- invalid login produces no sensitive account enumeration detail;
- successful verification establishes the same session model as passkey login;
- credential/session revocation remains backend-authoritative.

## Authorization boundary

Authentication answers `who is this?` and establishes session identity. It does not grant feature access by itself. Membership state and capability checks remain authoritative for protected resources.

A valid session for a removed/suspended membership therefore does not imply authorization to family resources.

## Security constraints

- TLS is required for non-local WebAuthn origins.
- WebAuthn private keys remain in the credential provider; server stores public credential material only.
- Passwords and bearer session secrets must never be logged.
- Stored session credentials are verifier/hash form, not reusable plaintext bearer tokens.
- Challenge consumption is atomic enough to prevent replay.
- Authentication failures use stable error classes without leaking secrets.
- Login endpoints require abuse/rate-control policy before production exposure.

## Failure states

Credential Manager unavailable, Digital Asset Links not verified, unsupported Android version/provider, challenge expired, challenge replayed, origin/RP mismatch, credential unknown/revoked, invalid password, session expired/revoked, initial Owner already enrolled, bootstrap token invalid, database unavailable.

## Non-goals

- social OAuth implementation;
- account/Owner recovery;
- MFA policy beyond passkey semantics;
- E2EE;
- enterprise SSO;
- multi-instance identity federation;
- final browser/web session profile;
- choosing a React Native passkey library before the Android spike.

## Success criterion

A READY self-hosted instance can securely transition its initial Owner from bootstrap authority to a normal passkey-first credential, and returning Android users can authenticate with passkeys or password fallback into revocable server sessions without a mandatory external IdP.
