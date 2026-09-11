---
id: PLAN-008-PUSH-NOTIFICATIONS
type: plan
status: active
depends_on:
  - SPEC-008-PUSH-NOTIFICATIONS
---

# Implementation Plan: Push Notifications

## Approach

Implement push as a provider-neutral notification module inside the FastAPI modular monolith, backed by PostgreSQL registrations/outbox and an asynchronous worker. Android obtains a native FCM token through `expo-notifications` and registers it against the already-authenticated MyHub Device.

## Architecture

```text
Business module
  -> NotificationIntent
  -> NotificationOutbox (PostgreSQL)
  -> Worker
  -> PushProvider port
  -> FcmHttpV1Provider
  -> FCM
  -> Android Device
```

Push never becomes the canonical source of a chat message, location event, membership state or other family state.

## Backend module

Proposed structure:

```text
services/api/src/myhub/modules/notifications/
├── domain.py
├── service.py
├── repository.py
├── provider.py
├── fcm.py
├── routes.py
└── worker.py
```

Infrastructure-specific persistence implementation may live under the existing infrastructure/database boundary if consistent with the modular-monolith conventions established during SPEC-001.

## Provider port

Conceptual contract:

```python
class PushProvider(Protocol):
    async def send(self, request: PushRequest) -> PushResult: ...
```

`PushResult` MUST classify outcomes sufficiently for worker policy:

```text
DELIVERED
RETRYABLE_FAILURE
INVALID_REGISTRATION
TERMINAL_FAILURE
```

FCM response/error details remain adapter concerns.

## Token registration API

Initial routes:

```text
PUT    /api/v1/devices/{device_id}/push-registration
DELETE /api/v1/devices/{device_id}/push-registration
```

`PUT` is idempotent for the same Device/token state and may replace the previous native token atomically.

Request does not choose tenant/user ownership. Those values are resolved from the authenticated Device/User context.

## Notification preference boundary

V0.1 needs only a narrow server-side preference model sufficient to suppress unwanted notification classes.

Minimum categories:

```text
chat_messages
family_events
```

If a broader preferences system is not yet implemented, defaults MUST be explicit in code/spec and not inferred from provider behavior.

## Outbox transaction boundary

The application service creating a durable business event SHOULD enqueue notification intent in the same PostgreSQL transaction when both writes occur in the same backend process/database.

For chat:

```text
BEGIN
  persist message
  persist recipient NotificationOutbox row(s)
COMMIT
```

Provider delivery occurs only after commit.

If a module cannot share the same transaction in a future architecture, that change requires explicit reliability design rather than silently doing fire-and-forget delivery.

## Worker claiming

Use PostgreSQL concurrency controls so multiple workers do not deliberately process the same available row simultaneously.

Candidate approach:

```sql
SELECT ...
FOR UPDATE SKIP LOCKED
```

Claim semantics MUST recover from worker crash/timeout. Exact lease/status implementation is an implementation detail but must be covered by integration tests.

## Retry policy

Retry only failures classified as transient/retryable.

Baseline:

```text
bounded attempts
exponential backoff
jitter
maximum delay cap
terminal state after budget exhaustion
```

Provider throttling/service-unavailable responses are retry candidates. Invalid/unregistered token responses invalidate the registration and are not retried indefinitely.

Exact timing constants belong in configuration and can be tuned without changing domain semantics.

## FCM authentication

Use FCM HTTP v1 authorization from the trusted backend environment.

Self-hosted non-Google deployments SHOULD provide a service-account credential file through an operator-controlled secret mount/environment reference (for example `GOOGLE_APPLICATION_CREDENTIALS`).

Do not embed service-account JSON in application source, Compose files committed to Git, or mobile configuration.

## Payload contract

Initial data payload should carry identifiers/routing hints rather than sensitive canonical content.

Conceptual chat payload:

```json
{
  "type": "chat.message.created",
  "version": "1",
  "message_id": "<uuid>",
  "channel_id": "<uuid>"
}
```

The client uses those identifiers to fetch/reconcile authorized API state.

If OS-visible title/body is added, privacy-safe generic text is the default baseline. Message preview requires a later explicit product/privacy decision.

## Android client

Proposed flow:

```text
Device registration complete
  -> request notification permission when contextually appropriate
  -> Notifications.getDevicePushTokenAsync()
  -> PUT MyHub push registration
  -> subscribe to addPushTokenListener(...)
  -> replace registration on rotation
```

Navigation from a notification MUST tolerate cold start and stale/deleted target content.

## Data migration

Add tables/indexes for:

```text
push_registrations
notification_outbox
notification_preferences (or equivalent narrow representation)
```

Important constraints:

- one current provider registration per Device/provider;
- indexed available/status fields for worker claiming;
- foreign keys to tenant/user/device where appropriate;
- uniqueness/idempotency key for logical notification intent when needed.

## Testing

### Unit

- provider outcome classification;
- retry schedule/budget;
- payload privacy contract;
- recipient filtering;
- token replacement semantics.

### Integration with PostgreSQL

- registration belongs to authenticated Device;
- revoked Device is excluded;
- message + outbox commit atomicity;
- rollback creates neither durable message notification intent nor partial outbox state;
- concurrent workers claim safely;
- retry state persists;
- invalid token deactivates registration.

### Provider adapter

Use deterministic HTTP mocks/fakes for FCM protocol behavior in normal CI. Do not require live Firebase credentials for repository CI.

### Android spike/manual validation

On a development build / real device validate:

- permission grant/deny;
- initial token registration;
- foreground/background receipt;
- cold-start navigation;
- token listener path;
- revoked Device no longer targeted;
- provider credentials missing/degraded behavior.

## Observability

Expose health/metrics sufficient to distinguish:

```text
MyHub healthy + push configured
MyHub healthy + push disabled/unconfigured
MyHub healthy + push degraded
```

No raw registration token or service-account secret in logs.

## Rollout

1. persistence + provider port;
2. token registration API;
3. outbox/worker;
4. FCM adapter;
5. chat notification intent integration;
6. Android registration/receipt/navigation;
7. real-device validation;
8. graph traceability + CI evidence.

## Open decisions preserved

- iOS delivery strategy;
- web push;
- notification body previews;
- future per-event granular preferences;
- encrypted-at-rest representation for provider registration tokens;
- whether Firebase Admin SDK later replaces/directly wraps the HTTP v1 adapter.
