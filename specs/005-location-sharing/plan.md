---
id: PLAN-005-LOCATION-SHARING
type: plan
status: active
depends_on:
  - SPEC-005-LOCATION-SHARING
---

# Implementation Plan: Location Sharing

## Mandatory order

Do not finalize production sampling values before completing the Android background-location spike. Implement the minimum instrumentation/spike harness first, measure, then feed results back into this plan/tasks.

## Mobile architecture

Initial Expo direction based on current official capabilities:

```text
expo-location
  +
expo-task-manager
  +
durable local queue (expo-sqlite candidate)
  +
DeviceCredentialStore from SPEC-004
```

Use an Expo development build, not Expo Go, for critical Android background validation.

Candidate feature structure:

```text
features/location/
├── permissions/
├── sharing-state/
├── collector/
├── queue/
├── sync/
├── quality/
└── diagnostics/
```

The background task definition must live at module/top-level scope as required by Expo TaskManager semantics.

## Android permission flow

User-driven sequence:

```text
explain why location is used
  -> request foreground permission
  -> explain background behavior/OS settings transition
  -> request background permission
  -> verify location services/capability
  -> explicit MyHub sharing activation
```

On Android 11+, background permission may require taking the user to system settings. On modern Android, long-running location sharing also interacts with the `location` foreground-service type and `FOREGROUND_SERVICE_LOCATION`; the app manifest/build configuration must match the targeted Android rules.

Permission denial never triggers repeated coercive prompts; surface settings/help instead.

## Background-location spike

Canonical artifact:

```text
docs/research/android-background-location-spike.md
```

Test at minimum:

- foreground;
- background;
- screen locked;
- app removed from recents;
- process terminated/force-stop distinction;
- reboot;
- Doze;
- battery optimization enabled/disabled;
- network loss/recovery;
- queue drain;
- GPS/location service disabled;
- coarse vs fine permission;
- background permission revoked;
- multiple manufacturers;
- at least one low/mid-tier device if available;
- battery use over representative windows.

Record actual sample cadence, capture latency, delivery latency, process survival, restart behavior, queue growth, synchronization duration and battery consumption.

## Local queue

Use a durable SQLite-backed queue unless the spike reveals a blocker. Schema concept:

```text
LocationQueueEvent
├── event_id UUID
├── captured_at
├── payload_json / typed columns
├── attempt_count
├── next_attempt_at
├── created_at
└── last_error_class nullable
```

Prefer typed columns or validated serialization; do not treat the queue as an unbounded log.

Queue limits and backpressure must be explicit. When limits are reached, prefer sampling/coalescing policy that is documented rather than crashing or silently growing storage forever.

### Pause policy

When the user pauses:

1. stop background updates;
2. transition local sharing state to PAUSED;
3. purge unsent location queue;
4. notify server of PAUSED when network is available/retry the state command separately from location event queue;
5. never restart collector from a remote refresh request.

The server also rejects new device-location ingestion when its sharing state is PAUSED, giving defense in depth.

## Server persistence

Conceptual tables:

```text
location_sharing_state
location_events
current_location
```

`location_events.id` has unique/idempotency constraint.

Current projection update condition:

```text
incoming captured_at > stored captured_at
OR deterministic accepted tie-break
```

Never order current projection by `received_at` alone.

## Ingestion API

Proposed:

```text
POST /api/v1/locations/events:batch
GET  /api/v1/locations/current
GET  /api/v1/locations/current/{user_id}
PUT  /api/v1/locations/sharing
GET  /api/v1/locations/sharing
```

`PUT /sharing` requires normal authenticated user authority. `POST events:batch` uses scoped Device principal.

Batch response should classify each client event as accepted, duplicate/idempotent or permanently rejected where safe, so local queue deletion is deterministic.

## Validation rules

At ingestion validate:

- Device principal;
- active membership;
- non-revoked device;
- device is selected location source;
- server sharing state ACTIVE;
- coordinates in legal ranges;
- non-negative accuracy where present;
- required captured_at;
- future clock-skew tolerance;
- batch size;
- payload size.

Server sets `received_at`.

## Freshness

Do not bake final thresholds until spike data exists. Provide one centralized `FreshnessPolicy` so thresholds are not duplicated across API/mobile/map.

Inputs may include:

```text
age since captured_at
sharing state
device revocation
last device contact
accuracy
known permission/capability status when reported
```

Output is a stable semantic state consumed by SPEC-006.

## Adaptive sampling

Use Expo/native options for accuracy, time/distance intervals/deferred updates where supported. The spike chooses profiles rather than one hard-coded loop.

Potential runtime profiles:

```text
STATIONARY
WALKING
FAST_MOVING
ACTIVE_FOLLOW
BATTERY_SAVER
```

Activity inference itself must be simple and evidence-backed; no driving analytics product is implied.

## Tests

Backend:

- consent/sharing-state transitions;
- device principal/source enforcement;
- paused ingestion rejection;
- event idempotency;
- batch retry behavior;
- captured vs received timestamps;
- late event cannot regress current projection;
- future clock-skew guard;
- tenant isolation;
- retention/purge hook baseline.

Mobile:

- permission-state machine;
- queue durability/retry;
- duplicate retry;
- pause purges unsent queue;
- source revoked/no source stops publishing;
- network recovery drain;
- stale status from local/server timestamps.

Real-device behavior belongs to the mandatory spike, not emulator-only test claims.

## Observability

Privacy-safe diagnostics:

```text
captured event count
queued event count
accepted/duplicate/rejected count
sync latency histogram
queue age
last successful sync time
permission/sharing state transitions
collector start/stop reason
```

Do not log coordinates or raw location payloads by default.

## Open decisions preserved

- final sampling values;
- final freshness thresholds;
- final history retention (24h remains recommendation, not frozen);
- visual route history;
- future temporary sharing durations;
- exact local queue encryption strategy beyond OS/app sandbox baseline;
- manufacturer-specific mitigations revealed by spike.
