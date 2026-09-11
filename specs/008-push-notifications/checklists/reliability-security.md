# Checklist: Push Reliability and Security

## Authorization and ownership

- [ ] Push registration ownership is derived from authenticated Device/User context.
- [ ] A revoked Device cannot register or receive push.
- [ ] Removed/suspended membership is excluded from recipient resolution.
- [ ] Push payload never grants authorization to canonical family data.

## Secrets

- [ ] FCM service-account credentials are server-only deployment secrets.
- [ ] Raw FCM registration tokens are excluded from normal logs.
- [ ] Provider credentials are absent from Git and mobile artifacts.
- [ ] Backups do not silently expose provider credentials without an explicit security decision.

## Privacy

- [ ] Precise location is absent from V0.1 push payloads.
- [ ] Authentication/session/invitation secrets are absent from payloads.
- [ ] Chat message body preview is disabled by default.
- [ ] Payload contains only minimal event identifiers/routing hints.

## Reliability

- [ ] Business state commits independently of provider availability.
- [ ] Notification intent is durably persisted before asynchronous delivery.
- [ ] Retry is bounded and only for retryable outcomes.
- [ ] Invalid/unregistered token is terminal and registration is invalidated.
- [ ] Concurrent workers cannot intentionally claim the same available outbox row.
- [ ] Worker crash leaves recoverable delivery state.
- [ ] Outbox idempotency prevents duplicate logical intent creation where required.

## Android client

- [ ] Native token comes from `getDevicePushTokenAsync()`.
- [ ] Token rotation listener updates the existing MyHub Device registration.
- [ ] Permission denial leaves the rest of MyHub usable.
- [ ] Notification response handles background and cold start.
- [ ] Stale/deleted target content is handled by API reconciliation.
- [ ] Real-device/development-build validation is documented.

## Operations

- [ ] Push can be explicitly unconfigured/degraded without failing core health.
- [ ] Metrics expose queue backlog, success, retry and terminal failure counts.
- [ ] Logs classify provider errors without leaking secrets.
- [ ] Live Firebase credentials are not required in repository CI.

## Engineering Graph

- [ ] Requirements map to `SPEC-008-PUSH-NOTIFICATIONS`.
- [ ] Every implementation task has graph-readable dependencies.
- [ ] Completed tasks gain CodeArtifact/Test evidence.
- [ ] Implementing PR traces to TASK-008 IDs.
- [ ] Graph drift/impact validation passes before merge.
