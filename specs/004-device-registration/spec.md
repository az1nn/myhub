---
id: SPEC-004-DEVICE-REGISTRATION
type: spec
status: active
requires:
  - REQ-DEVICE-001
  - REQ-DEVICE-002
  - REQ-DEVICE-003
  - REQ-DEVICE-004
  - REQ-DEVICE-005
  - REQ-DEVICE-006
  - REQ-DEVICE-007
  - REQ-DEVICE-008
  - REQ-DEVICE-009
  - REQ-DEVICE-010
critical_requirements:
  - REQ-DEVICE-001
  - REQ-DEVICE-002
  - REQ-DEVICE-004
  - REQ-DEVICE-005
  - REQ-DEVICE-006
  - REQ-DEVICE-008
constrained_by:
  - ADR-002
  - ADR-012
  - ADR-013
  - ADR-015
  - ADR-018
  - ADR-019
depends_on:
  - SPEC-002-AUTHENTICATION
---

# Feature Specification: Device Registration

## Problem

MyHub users may use multiple phones, tablets or future device types, but location and background operations must have an explicit, revocable source identity. A user session and a physical/app installation are different security objects and must not be conflated.

## Baseline

Approved architecture already establishes:

- one user may own multiple devices;
- device identity is explicit;
- one device may be designated as the location source;
- revoking a compromised/lost device does not transfer its identity to another device;
- Owner may revoke devices;
- backend authorization remains authoritative;
- location sharing itself remains user-consented and cannot be remotely reactivated.

## Requirements

### REQ-DEVICE-001 — Authenticated registration

A new device MUST be registered by an authenticated user/session or by an explicitly approved onboarding ceremony that resolves to that user. A client MUST NOT choose an arbitrary `user_id` or `tenant_id` and claim ownership.

The server derives ownership and tenant context from authenticated/onboarding authority.

### REQ-DEVICE-002 — Explicit install identity

Each app installation receives a unique server-side `Device` identity distinct from User and Session.

MyHub MUST NOT depend on invasive/global hardware identifiers such as IMEI, serial number or advertising ID to establish device identity.

A reinstall that loses local device credentials is treated as a new device unless a future secure device-recovery mechanism proves continuity.

### REQ-DEVICE-003 — Multiple devices

One User MAY have multiple active registered devices.

Device metadata may include a user-editable name plus non-sensitive operational fields such as platform, app version and last-seen timestamp. Metadata MUST NOT imply that last-seen equals live location freshness.

### REQ-DEVICE-004 — Scoped device credential

Registration MUST establish a device-bound proof suitable for narrowly scoped background operations without turning the device credential into a general family API session.

V0.1 may use a high-entropy opaque device secret stored only as verifier/hash on the server; an asymmetric device key is a compatible future evolution.

A device credential may authorize operations such as publishing that device's own location only after all relevant user/membership/consent checks pass.

### REQ-DEVICE-005 — Revocation

A device can be revoked by its owner and by an authorized membership with `devices.revoke` capability.

Revocation MUST immediately reject future device-authenticated background operations and MUST mark the device as revoked rather than silently reassigning its identity.

Revocation does not delete historical events already attributed to that device; retention policy governs those records.

### REQ-DEVICE-006 — Single explicit location source

For a given active user membership, at most one non-revoked Device may be selected as `location_source=true` at a time.

Changing the location source MUST be atomic and explicit.

Selecting a source does not itself grant OS location permission and does not enable MyHub location sharing.

### REQ-DEVICE-007 — Source ownership rule

A user may select among their own active devices as location source. Administrative device-revocation capability MUST NOT imply a capability to silently switch or activate another person's location source in a way that bypasses consent.

Any future administrative source-recovery behavior requires an explicit privacy/security decision.

### REQ-DEVICE-008 — Secure local storage

The mobile client MUST keep device credential material in platform-protected secure storage. It MUST NOT be committed to Git, stored in Markdown notes, printed to logs or placed in ordinary unprotected app preferences.

### REQ-DEVICE-009 — Idempotent registration/retry

Registration must define retry behavior so network retries do not accidentally create unbounded duplicate devices during one ceremony.

A stable client-generated registration attempt ID or equivalent server idempotency mechanism SHOULD be used.

### REQ-DEVICE-010 — Device status semantics

API/UI states MUST distinguish at least:

```text
active
revoked
```

Operational data may additionally indicate `last_seen_at`, `location_source` and platform metadata. `offline` is derived/freshness state and MUST NOT be persisted or displayed as a certainty without a defined threshold.

## User story — register this phone

As an authenticated family member, I want to register my phone so MyHub can identify this installation and later use it for permitted background operations.

Acceptance criteria:

- ownership comes from authenticated identity;
- server creates explicit Device record;
- device gets narrowly scoped credential material once;
- server stores only credential verifier/hash;
- device appears in the user's device list.

## User story — choose location source

As a member with more than one device, I want to explicitly choose which device may act as my location source.

Acceptance criteria:

- only own active devices are selectable through normal user flow;
- switch is atomic;
- at most one selected source remains;
- switch does not enable location sharing or OS permissions.

## User story — revoke lost phone

As a device owner or authorized Owner, I want to revoke a lost phone so its device credential can no longer publish background data.

Acceptance criteria:

- revocation is server-side;
- subsequent device-authenticated calls fail;
- Device retains revoked identity/audit association;
- another device is not silently promoted to location source;
- sharing consent is not silently changed.

## Authorization candidates

```text
devices.read
devices.register
devices.revoke
devices.select_location_source
```

Self-service policy and administrative capability policy remain centralized in the backend.

## Security/privacy constraints

- no global hardware tracking identifiers;
- device credential is scoped and revocable;
- raw device credential absent from logs/database after issuance;
- tenant/user ownership derived server-side;
- location source is not consent state;
- revoked device fails closed;
- device metadata must not be used to exaggerate location freshness.

## Failure states

Unauthenticated registration, duplicate retry, revoked session, removed membership, invalid device secret, revoked device, source switch race, source device revoked, secure storage unavailable, app reinstallation, database failure.

## Non-goals

- push notification token registration (SPEC-008);
- actual location collection/ingestion (SPEC-005);
- remote activation of location sharing;
- device-to-device identity transfer;
- MDM/device management;
- hardware attestation as a V0.1 requirement;
- watch/tablet-specific UX.

## Success criterion

An authenticated member can register multiple independent app installations, keep a revocable device identity on each, choose exactly one location source explicitly and revoke a lost device without weakening location consent or authorization boundaries.
