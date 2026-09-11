---
id: PLAN-007-FAMILY-CHAT
type: plan
status: active
depends_on:
  - SPEC-007-FAMILY-CHAT
---

# Implementation Plan: Family Chat

## Backend

Use `modules/chat/` in the modular monolith.

```text
ChatService
├── ChannelRepository
├── MessageRepository
├── AuthorizationPolicy
└── RealtimePublisher
```

Notification intent is emitted only after successful transaction/commit through the notification boundary from SPEC-008.

## Persistence

```text
family_channels
messages
```

One canonical family channel per tenant in V0.1. Enforce uniqueness in persistence rather than relying on bootstrap conventions alone.

Message idempotency key:

```text
(tenant_id, user_id, client_message_id)
```

Use UUID/ULID-like client message IDs generated before first send. Server owns canonical message ID and `created_at`.

## API baseline

```text
GET  /api/v1/chat/messages?after=<cursor>&limit=<n>
POST /api/v1/chat/messages
```

Response to POST is idempotent: same sender + same `client_message_id` resolves to the previously created message when payload is compatible. Reuse of the same idempotency key with different content must fail rather than mutate history silently.

## Pagination

Use stable cursor based on server-owned ordering key. Avoid offset pagination because history grows and reconnect needs deterministic “after last seen” semantics.

## Realtime

Publish after commit:

```json
{
  "type": "message.created",
  "version": 1,
  "tenant_id": "<uuid>",
  "event_id": "<uuid>",
  "occurred_at": "<timestamp>",
  "data": {
    "message": {}
  }
}
```

If event publishing fails, persisted message remains canonical and clients recover by HTTP.

## Mobile

Feature structure:

```text
features/chat/
├── api/
├── realtime/
├── queue/
├── state/
└── ui/
```

A small local pending-send queue is sufficient. It does not need to become a full offline message database in V0.1.

State reconciliation keys messages by canonical server ID when available and by `client_message_id` during pending/retry transition.

## Security

WebSocket connection/subscription must re-check session/membership semantics; membership removal must stop future authorized delivery. Avoid putting message content into observability logs.

## Push boundary

Persisted message creates a generic notification intent such as:

```text
family_chat.message_created
```

SPEC-008 chooses target devices, privacy-safe notification body and provider. Chat code does not call FCM/Expo directly.

## Retention

Keep a clearly marked configuration/policy seam. Do not implement automatic indefinite-retention assumptions as architecture. Final default remains blocked on the open chat-retention decision.

## Tests

- channel tenant uniqueness;
- authorized read/send;
- removed membership rejection;
- idempotent retry after simulated response loss;
- conflicting same client ID with changed body rejected;
- stable cursor pagination;
- realtime publish after commit;
- realtime failure does not roll back message;
- reconnect delta reconciliation;
- pending/sent/failed mobile state;
- message contents absent from normal logs.
