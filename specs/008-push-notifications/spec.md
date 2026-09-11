---
id: SPEC-008-PUSH-NOTIFICATIONS
type: spec
status: active
requires:
  - REQ-PUSH-001
  - REQ-PUSH-002
  - REQ-PUSH-003
  - REQ-PUSH-004
  - REQ-PUSH-005
critical_requirements:
  - REQ-PUSH-001
  - REQ-PUSH-002
  - REQ-PUSH-004
constrained_by:
  - ADR-003
  - ADR-013
  - ADR-015
  - ADR-018
  - ADR-019
depends_on:
  - SPEC-004-DEVICE-REGISTRATION
  - SPEC-007-FAMILY-CHAT
---

# Feature Specification: Push Notifications

## Problem

MyHub needs background notification delivery without turning notification providers into the source of truth, leaking sensitive family data in payloads, or making the self-hosted product depend on an OpenAI/MyHub-operated SaaS.

## Product boundary

V0.1 supports Android push notifications for relevant family events, initially including new family-chat activity. Push is a delivery optimization: the canonical state remains in MyHub's own API/database and clients reconcile after opening or reconnecting.

## Requirements

### REQ-PUSH-001 — Explicit device registration

A notification token MUST be bound to an authenticated, non-revoked MyHub Device. The backend MUST derive `tenant_id` and `user_id` from authorization context instead of trusting client-supplied ownership fields.

The same Device may rotate its native push token. Token replacement MUST NOT create duplicate logical notification destinations.

### REQ-PUSH-002 — Provider abstraction

Core application code MUST emit a provider-neutral notification intent. FCM-specific HTTP/authentication details MUST remain behind a `PushProvider` port.

V0.1 Android implementation uses the native FCM device token exposed through `expo-notifications`, not an Expo Push Token requirement.

MyHub MUST NOT require Expo Push Service for Android notification delivery.

### REQ-PUSH-003 — Reliable delivery boundary

Business transactions MUST NOT depend on successful push delivery.

When a committed business event requires notification, a durable notification/outbox record MUST be created transactionally with the relevant application state where practical. Provider delivery occurs asynchronously.

Transient provider failures SHOULD retry with bounded exponential backoff. Permanent token/provider errors MUST stop unbounded retry.

### REQ-PUSH-004 — Privacy-minimized payload

Push payloads MUST contain only the minimum information necessary to wake/navigate the client.

Normal V0.1 payloads MUST NOT contain:

- precise location coordinates;
- authentication/session/device credentials;
- invitation bearer secrets;
- full private message history;
- sensitive profile data unrelated to the notification.

Chat notification body preview is OFF by default in the spec baseline. The canonical message is fetched from MyHub after authorization.

### REQ-PUSH-005 — Revocation and stale-token handling

A revoked Device MUST no longer receive MyHub push notifications.

The backend MUST support:

- token replacement;
- explicit token removal;
- provider-reported invalid/unregistered token handling;
- user/device notification preference checks before enqueue/delivery.

## User story — receive family-chat activity

As a family member, I want to be notified when relevant chat activity happens while MyHub is backgrounded so I can open the app and retrieve the canonical message.

Acceptance criteria:

- notification targets only eligible devices for authorized members;
- sender's originating device is not notified for its own message by default;
- opening the notification navigates toward chat context;
- chat content is fetched from the MyHub API after app activation;
- duplicate worker attempts do not intentionally create duplicate outbox rows for one logical notification intent.

## User story — rotate a push token

As an Android user, I want MyHub to update the server when Android/FCM rotates my native token so notification delivery continues without registering a duplicate Device.

Acceptance criteria:

- token-listener update is associated with the existing authenticated Device;
- old token stops being used after replacement;
- token values are not emitted in normal application logs.

## Authorization

Device push-token registration/removal requires authenticated Device/User context. Notification fan-out resolves recipients from current memberships, device status and preferences at server side.

Push receipt alone grants no authorization to family data.

## Data model baseline

```text
PushRegistration
- id
- tenant_id
- user_id
- device_id
- provider
- token_ciphertext_or_protected_value
- token_fingerprint
- status
- created_at
- updated_at
- last_success_at
- invalidated_at

NotificationOutbox
- id
- tenant_id
- notification_type
- subject_type
- subject_id
- recipient_user_id
- payload
- status
- attempts
- available_at
- created_at
- delivered_at
- last_error_code
```

Exact encryption-at-rest mechanism remains governed by the broader secret-storage/security decisions; raw provider tokens MUST at minimum be treated as secrets and excluded from logs/diagnostics.

## Delivery semantics

The baseline is at-least-once worker execution with idempotent outbox processing.

```text
business commit
  -> notification intent/outbox
  -> worker claims item
  -> PushProvider.send(...)
  -> delivered | retryable failure | terminal failure
```

A push delivery success is not proof the user read the underlying event.

## Client behavior

Android client uses `expo-notifications` for permission/notification handling and obtains the native provider token with `getDevicePushTokenAsync()`.

Client MUST listen for native token rotation and re-register the new token with MyHub while preserving Device identity.

Meaningful push validation MUST run in an Android development/production build, not be inferred solely from a simulator-style JS test environment.

## Operational configuration

Self-hosted operator supplies FCM project/service credentials to the MyHub instance through deployment secrets/configuration.

Credentials MUST NOT be committed to Git, returned by public API, included in backup plaintext without an explicit backup-security decision, or sent to mobile clients.

If push credentials are absent or invalid, the MyHub instance remains otherwise usable; push status is degraded and observable rather than making core family state unavailable.

## Observability

Allowed metrics/events include:

- queued/delivered/retried/terminal-failure counts;
- delivery latency;
- provider error category;
- invalid-token count;
- outbox backlog age.

Normal logs MUST NOT contain raw push tokens or secret provider credentials.

## Failure states

Permission denied, native token unavailable, token rotation, revoked Device, removed membership, missing provider credentials, invalid service credentials, FCM unavailable, rate/throttle response, transient network failure, permanent invalid/unregistered token and worker crash between claim/send/update.

## Non-goals

V0.1 does not require iOS push, web push, marketing campaigns, notification analytics SaaS, topics as a domain abstraction, scheduled marketing, rich media, silent remote tracking activation, or a MyHub-operated notification relay.

## Success criterion

A self-hosted Android MyHub instance can reliably notify eligible family Devices about relevant events using its own configured FCM credentials while canonical state, authorization, privacy and product availability remain under MyHub control.
