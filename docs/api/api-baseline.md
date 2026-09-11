---
id: DOC-API-001
type: api-contract-baseline
status: active
---

# MyHub API Contract Baseline

Base prefix: `/api/v1`.

## Rules

- JSON over HTTPS.
- Authentication is required unless an endpoint is explicitly public/bootstrap.
- Backend authorization is authoritative.
- Relevant requests are resolved inside the authenticated family/tenant boundary.
- Retry-prone mutations SHOULD be idempotent.
- Location ingestion MUST be idempotent by event ID.
- Errors use stable machine-readable codes.

## Error envelope

```json
{
  "error": {
    "code": "INVITATION_EXPIRED",
    "message": "Invitation is no longer valid",
    "request_id": "<id>",
    "details": {}
  }
}
```

## Instance/bootstrap

```text
GET  /instance
GET  /instance/identity
GET  /health
POST /bootstrap/start
POST /bootstrap/complete
```

Exact bootstrap ceremony may be simplified during implementation while preserving the state/security invariants in SPEC-001.

## Authentication

```text
POST /auth/passkeys/register/options
POST /auth/passkeys/register/verify
POST /auth/passkeys/login/options
POST /auth/passkeys/login/verify
POST /auth/password/register
POST /auth/password/login
POST /auth/refresh
POST /auth/logout
```

Exact WebAuthn ceremony remains security-spec work.

## Invitations

```text
POST   /invitations
GET    /invitations/{token}/preview
POST   /invitations/{token}/accept
DELETE /invitations/{id}
```

Invitation preview MUST disclose only minimum safe information.

## Family/memberships

```text
GET    /family
PATCH  /family
GET    /members
GET    /members/{id}
PATCH  /members/{id}
DELETE /members/{id}
```

## Devices

```text
GET   /devices
POST  /devices
PATCH /devices/{id}
POST  /devices/{id}/revoke
POST  /devices/{id}/location-source
```

## Location

```text
POST /locations/events
GET  /locations/current
GET  /locations/current/{user_id}
GET  /locations/history/{user_id}
POST /locations/refresh/{user_id}
POST /locations/sharing
```

Location batch baseline:

```json
{
  "events": [
    {
      "id": "<uuid>",
      "device_id": "<uuid>",
      "latitude": -22.0,
      "longitude": -43.0,
      "accuracy_m": 10,
      "battery_pct": 68,
      "captured_at": "2026-09-10T18:00:00-03:00"
    }
  ]
}
```

The server sets `received_at`. Duplicate event IDs MUST NOT duplicate history. Current-location responses MUST include enough metadata to render freshness, capture time, device/offline status, paused state and accuracy. Consumers MUST NOT infer freshness from HTTP response time.

## Chat

```text
GET  /channels
GET  /channels/{id}/messages
POST /channels/{id}/messages
```

## Places

```text
GET    /places
POST   /places
GET    /places/{id}
PATCH  /places/{id}
DELETE /places/{id}
```

## Push

```text
POST   /push/devices
DELETE /push/devices/{id}
GET    /notification-preferences
PATCH  /notification-preferences
```

## Administration

```text
GET   /admin/status
GET   /admin/settings
PATCH /admin/settings
POST  /admin/backups
POST  /admin/restore
```

## Realtime

```json
{
  "type": "message.created",
  "version": 1,
  "tenant_id": "<uuid>",
  "event_id": "<uuid>",
  "occurred_at": "<timestamp>",
  "data": {}
}
```

Candidate V0.1 events:

```text
location.current.updated
location.sharing.changed
device.status.changed
message.created
message.updated
membership.created
membership.updated
membership.removed
```

WebSocket loss MUST be recoverable by refetching canonical HTTP state.
