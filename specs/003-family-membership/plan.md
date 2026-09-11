---
id: PLAN-003-FAMILY-MEMBERSHIP
type: plan
status: active
depends_on:
  - SPEC-003-FAMILY-MEMBERSHIP
---

# Implementation Plan: Family Membership & Invitations

## Architecture

Keep invitation and membership logic inside the FastAPI modular monolith:

```text
modules/memberships/
modules/invitations/
```

The feature consumes authentication primitives from SPEC-002 but does not duplicate credential verification logic.

## Persistence

Conceptual invitation model:

```text
Invitation
├── id
├── tenant_id
├── created_by_user_id
├── intended_role
├── token_hash
├── expires_at
├── consumed_at
├── consumed_by_user_id nullable
├── revoked_at
└── created_at
```

V0.1 uses `max_uses = 1` semantically; a generic reuse counter is unnecessary until a real reusable-invite requirement exists.

Membership already has the conceptual shape:

```text
Membership
├── id
├── tenant_id
├── user_id
├── role
├── status
├── created_at
└── updated_at
```

Use a database uniqueness constraint over the tenant/user identity boundary needed to prevent duplicate membership.

## Token design

Generate at least 256 bits of cryptographically secure random token material. Persist a one-way verifier/hash, not the bearer token.

A practical token can carry a non-secret invitation ID plus a secret component:

```text
invitation_id.secret
```

This permits indexed lookup by ID while validating only the secret verifier. The secret must be compared in constant time.

## Invitation creation

Proposed endpoint:

```text
POST /api/v1/invitations
```

Input includes intended role and optional supported expiry override within configured limits.

Response returns metadata plus raw invitation artifact once.

## Preview

Proposed endpoint:

```text
GET /api/v1/invitations/{token}/preview
```

If putting the raw token in an HTTP path proves too leak-prone for access logs, replace this route shape before implementation with a body-based validation endpoint. The contract must explicitly account for access-log/referrer exposure.

Preferred mobile flow keeps the bearer token inside the app and sends it only to an API validation/acceptance call over TLS.

## Acceptance with SPEC-002

For a new user:

```text
invite validated
  -> onboarding credential-registration options requested
  -> client creates passkey or password fallback credential
  -> server verifies credential
  -> transaction:
       lock invitation
       revalidate expiry/revocation/consumption
       create User
       create Membership
       persist credential
       consume invitation
       establish session
```

Where WebAuthn requires a multi-request ceremony, the server creates a short-lived onboarding context bound to invitation ID + intended user ceremony. The raw invitation token is not converted into a general session.

If credential verification fails, membership must not become active and the invitation must remain safely retryable unless the failure represents abuse/replay that invalidates the ceremony.

## Role policy

Normal invite role input:

```text
Adult
Member
```

Owner is excluded.

Role-to-capability mappings should be centralized rather than encoded in route conditionals.

## Removal

Proposed endpoint:

```text
DELETE /api/v1/members/{membership_id}
```

Within one transaction:

- authorize `members.remove`;
- tenant-scope the target;
- reject last-Owner removal;
- set membership removed/inactive state (prefer soft lifecycle over destroying audit-relevant relation immediately);
- subsequent resource authorization sees the new state.

Session revocation for the removed user may be performed as defense in depth, but correctness must not rely solely on session revocation because authorization must check membership state.

## QR/deep-link artifact

Preserve the conceptual server + token payload while allowing multiple presentation forms:

```text
QR JSON payload
Android App Link
copyable invite text/link
```

Do not put unrelated secrets in the payload.

Because Android App Links and passkeys already require Digital Asset Links for the instance domain, SPEC-002 and SPEC-003 should share that well-known association capability rather than invent separate domain-association mechanisms.

## Tests

- capability-protected invite creation;
- token entropy/verifier storage;
- raw token absent from persisted model/logs;
- expiry/revocation;
- single-use acceptance;
- concurrent double acceptance;
- duplicate membership rejection;
- role restrictions;
- minimal preview response;
- failed credential ceremony does not activate membership;
- successful onboarding creates exactly one membership;
- membership removal immediately changes authorization outcome;
- last Owner cannot be removed;
- joining does not activate location sharing.

## Open decisions preserved

- child profile/guardian policy;
- Owner transfer/recovery;
- final server identity verification protocol;
- exact deep-link token encoding;
- future multi-group or reusable invite semantics.
