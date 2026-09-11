# Location Sharing Privacy & Security Checklist

## Consent

- [ ] Location is visibly ACTIVE or PAUSED.
- [ ] Another member cannot remotely transition PAUSED → ACTIVE.
- [ ] Device source selection cannot activate sharing.
- [ ] OS permissions remain authoritative.
- [ ] Joining a family/registering a device does not activate sharing.
- [ ] Pausing stops collector and purges unsent local events under V0.1 policy.

## Device/tenant authority

- [ ] Ingestion derives tenant/user/device from validated Device principal.
- [ ] Device is non-revoked.
- [ ] Device is the explicitly selected location source.
- [ ] Membership is active.
- [ ] Server sharing state is ACTIVE.
- [ ] Cross-tenant payload ownership IDs cannot override principal scope.

## Offline/idempotency

- [ ] Event ID exists before first network attempt.
- [ ] Queue survives ordinary app restart.
- [ ] Retry cannot duplicate logical event.
- [ ] Batch response gives deterministic deletion/retry behavior.
- [ ] Queue has bounded storage/backpressure behavior.

## Freshness/time

- [ ] `captured_at` and `received_at` are separate.
- [ ] Late events cannot roll current projection backward.
- [ ] Future timestamp abuse cannot pin current location.
- [ ] Stale event is never presented as live because it arrived now.
- [ ] Approximate/coarse location is represented honestly.
- [ ] Battery value is understood as sample-time metadata, not live telemetry.

## Android reality

- [ ] Expo development build used for background validation.
- [ ] Foreground then background permission flow tested.
- [ ] Android 11+ settings transition tested.
- [ ] foreground-service location build config validated for targeted Android versions.
- [ ] locked screen tested.
- [ ] Doze/battery optimization tested.
- [ ] app termination/removal-from-recents tested.
- [ ] multiple manufacturers tested.
- [ ] reboot and network recovery tested.
- [ ] battery impact measured.

## Logging/retention

- [ ] Coordinates/raw payload absent from normal logs.
- [ ] Location retention is finite/configurable.
- [ ] V0.1 does not accidentally expose route history APIs/UI.
- [ ] purge/retention interaction is tested.
