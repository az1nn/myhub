---
id: PLAN-004-DEVICE-REGISTRATION
type: plan
status: active
depends_on:
  - SPEC-004-DEVICE-REGISTRATION
---

# Implementation Plan: Device Registration

## Backend module

Use `modules/devices/` in the FastAPI modular monolith.

```text
DeviceService
├── DeviceRepository
├── DeviceCredentialIssuer
└── AuthorizationPolicy
```

## Persistence

Extend Device concept with:

```text
id
 tenant_id
 user_id
 name
 platform
 app_version
 credential_hash
 location_source
 registered_at
 last_seen_at
 revoked_at
```

Do not persist plaintext device secret.

Enforce at most one active location source per user. PostgreSQL partial uniqueness is preferred when practical, backed by a transaction/lock in the source-switch service.

## Device credential

V0.1 recommendation:

```text
device token = device_id.secret
```

- `device_id` supports indexed lookup;
- `secret` contains >=256 bits random entropy;
- server persists hash/verifier of the secret;
- compare secret verifier in constant time;
- client receives the raw credential once and stores it in Android secure storage.

Device authentication middleware produces a narrow principal such as:

```text
DevicePrincipal(device_id, user_id, tenant_id)
```

It does not automatically grant normal member API capabilities.

## Registration

Proposed endpoint:

```text
POST /api/v1/devices
```

Requires authenticated user session. Server ignores/rejects client-supplied ownership IDs.

Input:

```text
name
platform
app_version
registration_attempt_id
```

Output includes Device metadata and one-time device credential.

## Listing

```text
GET /api/v1/devices
```

Normal member sees own devices. Administrative visibility for other members' device metadata must be capability-scoped and data-minimal.

## Source selection

```text
POST /api/v1/devices/{device_id}/location-source
```

Transaction:

```text
verify own active device
lock source set for user
clear previous source
set selected source
commit
```

No call to location-sharing activation belongs in this transaction.

## Revocation

```text
POST /api/v1/devices/{device_id}/revoke
```

Self-revoke or `devices.revoke` capability. If revoked device is current source, clear source and leave the user with no location source until they explicitly choose another one.

## Mobile storage

Define a `DeviceCredentialStore` port in mobile shared storage and implement it using the platform secure credential/key storage available in the chosen Expo development build. Generic AsyncStorage is not acceptable for the raw device secret.

## Tests

- authenticated ownership derivation;
- registration idempotency;
- token entropy/hash storage;
- no raw token logging;
- multiple device registration;
- atomic source selection;
- source race handling;
- source switch never toggles sharing consent;
- revoke own device;
- authorized Owner revocation;
- unauthorized cross-user revoke rejection;
- revoked token rejected;
- revoking current source leaves no source;
- tenant isolation.

## Engineering Graph

Implementation paths/tests are added to task metadata as tasks complete. Graph conflict analysis is especially relevant because SPEC-004 and SPEC-005 will share device-principal/authentication integration points.
