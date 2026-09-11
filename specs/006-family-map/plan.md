---
id: PLAN-006-FAMILY-MAP
type: plan
status: active
depends_on:
  - SPEC-006-FAMILY-MAP
---

# Implementation Plan: Family Map

## Map engine

Initial evaluation target:

```text
@maplibre/maplibre-react-native
```

Current MapLibre React Native documentation supports Expo through a config plugin/custom native build and explicitly states it cannot run inside Expo Go. This aligns with MyHub already requiring development builds for background location.

Do not use demo tiles/styles in production. Introduce a `MapStyleProvider` configuration boundary:

```text
style_url
optional attribution/config metadata
```

A later operator UX can simplify provider selection without hard-coding a centralized author-operated service.

## Client data flow

```text
GET current-location snapshot
    -> normalize MemberMapState
    -> render markers/cards

WebSocket current-location event
    -> validate version/tenant/member identity
    -> merge if newer by captured_at/version

WebSocket reconnect
    -> GET snapshot
    -> reconcile
```

Do not let realtime arrival order override the timestamp/current-location ordering guaranteed by SPEC-005.

## State model

Create one typed view model:

```text
MemberMapState
├── userId
├── displayName
├── coordinate nullable
├── capturedAt nullable
├── receivedAt nullable
├── freshness
├── accuracyM nullable
├── batteryPct nullable
└── sharingStatus
```

The map component consumes this view model rather than raw API records.

## UI structure

```text
MapScreen
├── status/realtime banner
├── map viewport
│   └── member markers
├── member selector/list
└── selected member card
```

The member list/status remains useful if tiles fail.

## Caching

Cache only enough current map state for startup continuity. Cached coordinates must retain `captured_at` and freshness calculation; cache age can never reset freshness.

Clear tenant/user-scoped sensitive cache on logout or instance switch.

## Realtime

Candidate event from architecture baseline:

```text
location.current.updated
location.sharing.changed
device.status.changed
```

HTTP remains recovery source of truth.

## Tests

- authorized snapshot only;
- stale timestamp rendering;
- approximate rendering;
- paused last-known treatment;
- late realtime update rejected if older;
- reconnect snapshot reconciliation;
- viewer map opening does not enable sharing;
- tile failure retains textual family status;
- logout/instance switch clears scoped coordinate cache.

## Research reference

Current MapLibre React Native docs:
- https://maplibre.org/maplibre-react-native/docs/setup/expo/
- https://maplibre.org/maplibre-react-native/docs/setup/getting-started/

The package requires a custom native rebuild for Expo and expects production users to provide their own style/tiles or a provider.
