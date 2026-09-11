# Research: Push Notifications

## Research date

2026-09-11.

## Question 1 — Can Expo be used without Expo Push Service?

Yes.

Current Expo documentation states that `expo-notifications` is push-service agnostic and that a native FCM/APNs token can be obtained with:

```ts
Notifications.getDevicePushTokenAsync()
```

That token can be sent to the application's own backend and used with FCM/APNs directly.

References:

- https://docs.expo.dev/push-notifications/sending-notifications-custom/
- https://docs.expo.dev/push-notifications/faq/
- https://docs.expo.dev/versions/latest/sdk/notifications/

### Decision

For Android V0.1, MyHub uses the native FCM token rather than requiring `ExpoPushToken` / Expo Push Service.

This preserves Expo as the React Native application framework while keeping notification delivery under the self-hosted instance's control.

## Question 2 — How does the backend authorize FCM HTTP v1 requests?

Firebase documentation requires OAuth 2.0 authorization for FCM HTTP v1. A trusted server environment may use Application Default Credentials or a service-account credential to mint short-lived access tokens.

For non-Google self-hosting, Firebase documents service-account JSON credentials and recommends supplying their path with `GOOGLE_APPLICATION_CREDENTIALS` rather than embedding the private key in application code.

References:

- https://firebase.google.com/docs/cloud-messaging/server-environment
- https://firebase.google.com/docs/cloud-messaging/send/v1-api

### Decision

The MyHub backend is the trusted FCM caller. Operator credentials are server-side deployment secrets only.

The mobile client never receives Firebase service-account credentials.

## Question 3 — What reliability behavior is required?

Firebase's server-environment guidance explicitly calls for a trusted environment that can securely store authorization credentials/registration tokens and resend with exponential backoff when appropriate.

### Decision

Provider delivery is asynchronous behind a durable PostgreSQL outbox. Retry policy is bounded and only applies to failures classified as retryable.

Business transactions cannot roll back because FCM is unavailable.

## Question 4 — How should token rotation be handled?

Current Expo Notifications API includes a push-token listener intended for token changes while the application is running.

### Decision

MyHub treats the notification token as mutable provider routing data attached to an existing Device identity.

Token rotation updates that Device's registration instead of creating a new MyHub Device.

## Question 5 — Should push payload contain the canonical event content?

No requirement in the product baseline needs that coupling, and doing so would increase exposure of family data through OS/provider notification infrastructure.

### Decision

Push payload contains minimal event identifiers/routing hints. Canonical chat/event state is fetched from MyHub after the client opens/reconciles.

Message-body preview remains disabled by default until explicitly decided.

## Question 6 — Is FCM a structural business dependency?

Android remote push inherently needs a platform push path, but MyHub should isolate this integration rather than make FCM semantics part of core modules.

### Decision

`PushProvider` is a backend port. FCM HTTP v1 is the first Android adapter.

If credentials are absent, core MyHub remains functional and reports push as unconfigured/degraded.

## Non-decisions

Research does not yet choose:

- iOS push implementation;
- web push;
- Firebase Admin SDK vs a small direct HTTP v1 adapter as the permanent implementation;
- provider-token encryption-at-rest mechanism;
- notification message previews;
- marketing/analytics integrations.

Those are outside V0.1 or require separate security/product decisions.
