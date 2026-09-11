---
id: SPEC-007-FAMILY-CHAT
type: spec
status: active
requires:
  - REQ-CHAT-001
  - REQ-CHAT-002
  - REQ-CHAT-003
  - REQ-CHAT-004
  - REQ-CHAT-005
  - REQ-CHAT-006
  - REQ-CHAT-007
  - REQ-CHAT-008
  - REQ-CHAT-009
critical_requirements:
  - REQ-CHAT-001
  - REQ-CHAT-002
  - REQ-CHAT-003
  - REQ-CHAT-004
  - REQ-CHAT-005
  - REQ-CHAT-008
constrained_by:
  - ADR-002
  - ADR-012
  - ADR-018
  - ADR-019
depends_on:
  - SPEC-002-AUTHENTICATION
  - SPEC-003-FAMILY-MEMBERSHIP
---

# Feature Specification: Family Chat

## Problem

MyHub needs fast family communication that complements location context without becoming a general-purpose messaging platform. The first slice must be reliable enough for short family notes while keeping authorization, offline/retry behavior and realtime recovery explicit.

## Requirements

### REQ-CHAT-001 — One family channel in V0.1

V0.1 has one principal text channel per tenant/family. Direct messages, multiple user-created channels and topic spaces are not part of this release.

The family channel is created/available as part of tenant operation and is always tenant-scoped.

### REQ-CHAT-002 — Backend-authorized access

Reading requires `messages.read`; sending requires `messages.send` or equivalent backend policy.

An authenticated session without an active authorized Membership MUST NOT read or send family messages.

### REQ-CHAT-003 — Text-only durable messages

V0.1 messages contain text content and server-owned identity/timestamps. Attachments are excluded.

Conceptual shape:

```text
Message
├── id
├── tenant_id
├── channel_id
├── user_id
├── client_message_id
├── content
└── created_at
```

The server derives `tenant_id` and sender identity rather than trusting client ownership fields.

### REQ-CHAT-004 — Idempotent send/retry

The client MUST assign a stable `client_message_id` before first send. Retrying a transiently failed send MUST return/resolve the same logical message rather than duplicate it.

Uniqueness is scoped so two different users cannot collide accidentally while one user's retry remains idempotent.

### REQ-CHAT-005 — HTTP truth + realtime delivery

HTTP pagination is the recoverable source for persisted message history. WebSocket events provide low-latency delivery.

On reconnect, the client MUST fetch/reconcile messages after its last known server cursor rather than assume no events were missed.

### REQ-CHAT-006 — Explicit delivery UI state

Outgoing messages distinguish at least:

```text
pending
sent
failed
```

A locally queued/pending message MUST NOT be visually indistinguishable from a server-persisted message.

Transient failures can be retried with the same `client_message_id`.

### REQ-CHAT-007 — Stable ordering/pagination

Server pagination MUST use a deterministic cursor/order. `created_at` plus immutable message ID or an equivalent server sequence is acceptable.

WebSocket arrival order alone MUST NOT define durable history order.

### REQ-CHAT-008 — Notification intent after persistence

A successfully committed message MAY generate a push-notification intent for other eligible members through SPEC-008.

Push delivery failure MUST NOT roll back or duplicate the chat message. Notification is downstream of durable message creation.

### REQ-CHAT-009 — Privacy and retention boundary

Message content MUST NOT be written to application logs/telemetry by default.

The final chat retention policy remains an open product decision from the handoff. This spec MUST NOT silently claim infinite retention or introduce destructive purge behavior without that decision. Implementation must expose retention as an explicit unresolved configuration/policy item before production release.

## User story — send a family note

As a family member, I want to send a short message to the family channel so everyone can see it quickly.

Acceptance criteria:

- sender has active membership and send permission;
- message persists once;
- retry cannot duplicate it;
- sender sees pending/sent/failed honestly;
- connected family clients receive realtime event;
- disconnected clients recover message through HTTP later.

## User story — reconnect

As a member who lost connectivity, I want chat to reconcile when I reconnect so missed realtime messages appear without duplicating my pending sends.

Acceptance criteria:

- client retains last server cursor;
- reconnect triggers history delta fetch;
- local pending messages retain client IDs;
- server idempotency prevents duplicates;
- durable server ordering wins over event arrival order.

## Realtime event

Candidate versioned event:

```text
message.created
```

Payload contains only the data already authorized for channel participants and enough identity/version metadata for reconciliation.

## Content constraints

Implementation must define a reasonable UTF-8 message size limit and reject oversized content with a stable validation error. Exact size is implementation configuration, not an invitation to support arbitrary files/base64 payloads.

## Security/privacy constraints

- tenant/member authorization on every read/send;
- sender identity server-derived;
- message content absent from normal logs;
- message push preview behavior is owned by SPEC-008 privacy policy;
- WebSocket subscription is authorized and invalidated when membership becomes inactive;
- no geofence/location event automatically floods the chat;
- no E2EE claim unless a later architecture decision implements it end-to-end.

## Failure states

Offline send, request timeout after server commit, duplicate retry, revoked/expired session, removed membership, WebSocket disconnect, cursor recovery, database failure, oversized message, malformed UTF-8/input, downstream push failure.

## Non-goals

- direct messages;
- attachments/media;
- voice/video;
- presence/typing indicators;
- read receipts;
- message edit/delete;
- reactions/reply/pins in V0.1;
- E2EE;
- search;
- location/geofence events as automatic chat messages.

## Success criterion

A family member can reliably send and receive short text notes in one tenant-scoped channel with idempotent retries and HTTP/realtime reconciliation, without adding general-messenger complexity to V0.1.
