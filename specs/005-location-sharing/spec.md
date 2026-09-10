---
id: SPEC-005-LOCATION-SHARING
type: spec
status: active
requires:
  - REQ-LOC-001
  - REQ-LOC-002
  - REQ-LOC-003
  - REQ-LOC-004
  - REQ-LOC-005
  - REQ-LOC-006
  - REQ-LOC-007
  - REQ-LOC-008
  - REQ-LOC-009
  - REQ-LOC-010
  - REQ-LOC-011
  - REQ-LOC-012
critical_requirements:
  - REQ-LOC-001
  - REQ-LOC-002
  - REQ-LOC-003
  - REQ-LOC-004
  - REQ-LOC-005
  - REQ-LOC-006
  - REQ-LOC-007
  - REQ-LOC-008
  - REQ-LOC-009
  - REQ-LOC-011
constrained_by:
  - ADR-002
  - ADR-013
  - ADR-014
  - ADR-015
  - ADR-018
  - ADR-019
depends_on:
  - SPEC-004-DEVICE-REGISTRATION
---

# Feature Specification: Location Sharing

## Problem

MyHub needs useful family location without covert tracking, stale-location confusion or battery-destructive fixed GPS polling. Android background execution is constrained by OS permissions, foreground-service rules and vendor behavior, so product semantics must describe what the system can actually guarantee.

## Baseline

Approved architecture establishes:

- location sharing is always explicit and visible;
- no stealth mode;
- another member cannot silently enable a user's GPS;
- paused sharing cannot be remotely reactivated;
- OS permissions are authoritative;
- location collection continues in background only within platform limitations;
- collection uses adaptive rather than rigid polling;
- offline events queue locally and synchronize later;
- `captured_at` and `received_at` remain distinct;
- current location is separate from location history;
- stale historical coordinates never masquerade as current;
- one explicit Device is the user's location source;
- Android background-location behavior requires an empirical spike before final sampling values are accepted.

## Requirements

### REQ-LOC-001 — Explicit sharing state

Location sharing MUST have an explicit server-visible/user-visible state. V0.1 implements at minimum:

```text
ACTIVE
PAUSED
```

The domain may reserve `TEMPORARY` for later time-bounded sharing, but V0.1 MUST NOT expose temporary sharing UX until expiry semantics are fully implemented.

Only the sharing user may normally transition their own state from PAUSED to ACTIVE. Administrative permissions MUST NOT silently reactivate another person's sharing.

### REQ-LOC-002 — OS permission authority

The app MUST respect actual Android location service/permission state. MyHub sharing state cannot override OS denial, approximate-only permission, background denial, battery restrictions or a terminated app.

UI/API status MUST be able to distinguish MyHub consent state from observed device capability.

### REQ-LOC-003 — Explicit source device

Only the user's active non-revoked Device selected as `location_source=true` may publish that user's location under the normal background pipeline.

A valid device credential from another device does not make it the current location source.

### REQ-LOC-004 — Device-scoped ingestion authority

Background location ingestion uses the scoped Device identity from SPEC-004. The server derives tenant/user/device from the validated device principal rather than trusting ownership IDs supplied in the payload.

Ingestion MUST also check active membership, non-revoked device, selected location source and sharing state.

### REQ-LOC-005 — Durable offline queue

While sharing is ACTIVE, captured locations MUST first enter a durable local queue before or as part of network transmission so transient connectivity loss does not silently discard all movement.

Each queued event receives a stable client-generated event ID before first transmission.

V0.1 privacy policy for pausing: when the user explicitly pauses sharing, collection stops and unsent location events still present only in the local queue are purged by default. This favors the latest consent decision over later disclosure of data that never left the device. Already accepted server events remain governed by server retention.

### REQ-LOC-006 — Idempotent event ingestion

Server ingestion MUST be idempotent by location event ID. Retrying the same event or batch MUST NOT create duplicate logical events or duplicate current-location transitions.

Batch ingestion SHOULD permit efficient draining after reconnect while enforcing a documented batch-size limit.

### REQ-LOC-007 — Timestamp truth

Each event preserves:

```text
captured_at  = when the device says the sample was captured
received_at  = when the server accepted the event
```

Late synchronization MUST NOT overwrite a newer `current_location` merely because `received_at` is recent.

The current-location projection is ordered primarily by accepted `captured_at`, with deterministic tie-breaking. Events with timestamps implausibly far in the future relative to server receipt MUST be rejected or quarantined from the current projection so clock manipulation cannot pin a false future location.

### REQ-LOC-008 — Current-location projection

`current_location` is a read-optimized projection separate from retained location events/history.

At minimum it exposes:

```text
tenant_id
user_id
device_id
location_event_id
latitude
longitude
accuracy_m
battery_pct optional
captured_at
received_at
```

Freshness is derived from timestamps/device/sharing state; it is not an assertion that the person is still physically at that coordinate.

### REQ-LOC-009 — Freshness and quality semantics

Consumers MUST be able to represent at least:

```text
fresh
approximate
stale
offline/unknown capability
paused
unavailable
```

Exact time/accuracy thresholds are not frozen by this spec; they must be measured and documented before SPEC-006 map UX is finalized.

A delayed historical event MUST never be labeled as a live update solely because it arrived recently.

### REQ-LOC-010 — Adaptive collection

The collector MUST support adaptive configuration based on motion/activity, desired accuracy, time/distance deferral and active map-follow context where supported.

The handoff hypotheses are experimental starting points only:

```text
stationary        ~5–10 min
walking           ~1–2 min
fast/vehicle      ~20–60 sec
active follow     temporarily higher
```

No production acceptance criterion may require these exact numbers until the Android spike measures reliability and battery impact on real devices/vendors.

### REQ-LOC-011 — Background reality is visible

The product MUST NOT claim uninterrupted Android tracking when the OS cannot provide it.

If the app is terminated, background permission is unavailable, the device is offline, location services are disabled or vendor battery management prevents execution, the last accepted coordinate ages naturally into stale/offline/unavailable states.

Restart/recovery MUST resume only when MyHub sharing remains ACTIVE and OS permissions still allow it.

### REQ-LOC-012 — Data minimization and retention boundary

The location event payload contains only fields justified by location quality/reliability:

```text
id
latitude
longitude
accuracy_m
altitude_m optional
speed_mps optional
heading_deg optional
battery_pct optional
source
captured_at
```

Tenant/user/device ownership is server-derived.

Visual route history is not part of this V0.1 spec. Persisted event retention MUST be finite and configurable; the project's current recommendation of 24 hours remains provisional until the dedicated history/retention decision is closed.

## User story — enable sharing

As a member, I want to explicitly enable my location on this phone so my family can see a reasonably fresh position while Android permits collection.

Acceptance criteria:

- selected location source is this active device;
- required OS permission flow is explained and user-driven;
- server sharing state becomes ACTIVE only by user action;
- collector begins only after state + permission checks;
- UI exposes that background behavior is subject to OS/device restrictions.

## User story — pause immediately

As a member, I want to pause sharing so MyHub stops collecting and stops later disclosing queued unsent positions from this device.

Acceptance criteria:

- server state transitions to PAUSED by user action;
- local collector stops;
- unsent local queue is purged under V0.1 privacy policy;
- device cannot continue accepted background ingestion while paused;
- another member cannot remotely resume sharing;
- previously stored server events age/expire according to retention and are never presented as current without freshness context.

## User story — reconnect after network loss

As a member whose phone remained offline while sharing was ACTIVE, I want queued samples to synchronize when connectivity returns so recent movement is not lost.

Acceptance criteria:

- each event keeps original `captured_at`;
- server supplies `received_at`;
- retries are idempotent;
- newer current projection is never rolled back by late samples;
- batch failure exposes retryable vs permanent failures.

## Authorization/consent boundary

`locations.share` capability means the authenticated user is allowed to operate the location-sharing feature; it does not represent active consent by itself.

Correct ingestion therefore requires all of:

```text
valid device principal
active membership
non-revoked device
selected location source
sharing_state = ACTIVE
OS/client capture permission at collection time
```

## Failure states

Permission denied, approximate-only permission, background permission denied, location services disabled, app terminated, vendor task killing, no source device, source device revoked, sharing paused, device token revoked, offline queue full/corrupt, network loss, duplicate event, clock skew/future timestamp, invalid coordinate/accuracy, server unavailable, partial batch rejection.

## Non-goals

- visual route/history UI;
- geofencing/Places (later spec);
- location-based reminders;
- crash detection;
- driving analytics;
- covert/remote tracking activation;
- final universal sampling intervals before empirical spike;
- guaranteed restart after Android process termination;
- exact map freshness UI (SPEC-006).

## Success criterion

A consenting member can select one registered device, enable background-capable Android location, safely queue and synchronize idempotent samples, and expose a truthful current-location projection that degrades to stale/paused/unavailable states when reality prevents fresh tracking.
