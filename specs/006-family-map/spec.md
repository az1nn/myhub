---
id: SPEC-006-FAMILY-MAP
type: spec
status: active
requires:
  - REQ-MAP-001
  - REQ-MAP-002
  - REQ-MAP-003
  - REQ-MAP-004
  - REQ-MAP-005
  - REQ-MAP-006
  - REQ-MAP-007
  - REQ-MAP-008
  - REQ-MAP-009
critical_requirements:
  - REQ-MAP-001
  - REQ-MAP-002
  - REQ-MAP-003
  - REQ-MAP-004
  - REQ-MAP-005
  - REQ-MAP-008
constrained_by:
  - ADR-002
  - ADR-007
  - ADR-012
  - ADR-014
  - ADR-015
  - ADR-018
  - ADR-019
depends_on:
  - SPEC-005-LOCATION-SHARING
---

# Feature Specification: Family Map

## Problem

Family members need one clear map surface that answers where permitted members were last located without turning stale, approximate, paused or offline data into false certainty.

## Requirements

### REQ-MAP-001 — Authorized family snapshot

The map MUST load family location state only for members the authenticated viewer is authorized to see through backend `locations.view` policy. Tenant scope is mandatory.

A client MUST NOT infer authorization from receiving a user ID elsewhere in the app.

### REQ-MAP-002 — Freshness is part of the marker

Every rendered member location MUST communicate freshness/status together with the coordinate. A naked marker that looks live without timestamp/state is not acceptable.

Supported semantic states consume SPEC-005 output:

```text
fresh
approximate
stale
offline/unknown capability
paused
unavailable
```

### REQ-MAP-003 — Captured time, not arrival illusion

The map displays age based on the location sample's accepted `captured_at`, not merely WebSocket receipt or API fetch time.

A delayed sync event therefore cannot appear as “updated now” if it was captured earlier.

### REQ-MAP-004 — Paused behavior

When a member is PAUSED, the UI MUST visibly say sharing is paused.

If a previously shared coordinate is still retained/authorized, V0.1 MAY show it only as a last-known coordinate with its captured timestamp and paused/stale treatment. The UI MUST NOT imply that the person remains there.

### REQ-MAP-005 — Snapshot + realtime recovery

Initial/current truth comes from HTTP current-location snapshot. WebSocket updates improve freshness but are not the sole source of state.

On reconnect, app MUST re-fetch/reconcile snapshot so missed WebSocket events do not permanently desynchronize the map.

### REQ-MAP-006 — Member card

A selected member card may show data already supplied by the authorized current-location projection, such as:

```text
display name
freshness label
captured time
accuracy/approximate indicator
battery at sample time (optional)
nearby named Place when available later
```

Battery MUST be understood as sample-time metadata, not live battery telemetry.

### REQ-MAP-007 — No viewer location requirement

Viewing family members on the map MUST NOT require enabling the viewer's own location sharing. The viewer may browse the family map while their sharing remains PAUSED, subject to authorization policy.

### REQ-MAP-008 — Map provider privacy boundary

MyHub MUST NOT require a centrally operated map service controlled by the MyHub authors.

The rendering engine/style/tile source MUST be configurable enough to support family-selected third-party or self-hosted map infrastructure. Production MUST NOT rely on MapLibre demo tiles.

Map/tile requests may reveal viewport geography to the configured tile provider; self-hosting documentation MUST disclose this privacy boundary.

### REQ-MAP-009 — Truthful empty/error states

The map MUST explicitly handle:

```text
member has never shared
sharing paused
location unavailable
location stale
map tiles unavailable
realtime disconnected
API unavailable
```

Tile rendering failure MUST NOT erase the textual location status/member list needed to understand the state.

## Rendering direction

Use MapLibre React Native as the initial open-source map-engine evaluation target because it supports React Native/Expo custom-native-code builds and does not structurally bind MyHub to Google Maps. Final production style/tile provider remains configurable.

## User story — open family map

As a family member, I want to open the map and quickly understand where each permitted member was last located and how trustworthy/fresh that information is.

Acceptance criteria:

- authorized current snapshot loads;
- markers carry status/freshness semantics;
- delayed/stale data is visibly stale;
- tapping a member reveals captured time and available quality metadata;
- realtime updates update the appropriate marker;
- reconnect reconciles through HTTP.

## User story — view while I am paused

As a member who paused my own location, I still want to view family locations I am authorized to see without MyHub silently reactivating my GPS.

Acceptance criteria:

- opening map does not start location sharing;
- viewer's paused state remains unchanged;
- their own marker/status visibly indicates PAUSED according to authorized last-known policy.

## Security/privacy constraints

- backend filters authorized members;
- no hidden client request may activate sharing;
- tile provider is a disclosed external privacy boundary;
- precise coordinates are not emitted to analytics/logs;
- stale positions remain stale through realtime/UI transformations;
- cached map state is cleared/scoped appropriately on logout/family change.

## Non-goals

- route/history playback;
- navigation/directions;
- traffic;
- driving analytics;
- offline map packages;
- geofence editing (SPEC-009);
- SOS;
- a mandatory MyHub-hosted tile service.

## Success criterion

The Android client presents one truthful, authorized family map whose visual state cannot make an old/paused/approximate coordinate look live and whose map infrastructure does not create a mandatory centralized MyHub service.
