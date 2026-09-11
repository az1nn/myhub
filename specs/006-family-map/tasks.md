---
id: TASKSET-006-FAMILY-MAP
type: tasks
status: active
spec_id: SPEC-006-FAMILY-MAP
depends_on:
  - PLAN-006-FAMILY-MAP
task_metadata:
  TASK-006-01:
    priority: 1
    depends_on: []
  TASK-006-02:
    priority: 1
    depends_on: []
  TASK-006-03:
    priority: 2
    depends_on: [TASK-006-01]
  TASK-006-04:
    priority: 2
    depends_on: [TASK-006-01, TASK-006-02]
  TASK-006-05:
    priority: 3
    depends_on: [TASK-006-03, TASK-006-04]
  TASK-006-06:
    priority: 3
    depends_on: [TASK-006-04]
  TASK-006-07:
    priority: 4
    depends_on: [TASK-006-05, TASK-006-06]
  TASK-006-08:
    priority: 5
    depends_on: [TASK-006-07]
  TASK-006-09:
    priority: 6
    depends_on: [TASK-006-08]
---

# Tasks: Family Map

- [ ] TASK-006-01 Integrate MapLibre React Native in Expo development build and define configurable production style/tile boundary.
- [ ] TASK-006-02 Define typed `MemberMapState` and API/realtime adapters preserving freshness semantics.
- [ ] TASK-006-03 Implement Map screen, member markers and selected-member card with explicit freshness/accuracy/paused states.
- [ ] TASK-006-04 Implement HTTP snapshot + WebSocket update + reconnect reconciliation.
- [ ] TASK-006-05 Implement sensitive current-map cache with preserved captured timestamps and logout/instance clearing.
- [ ] TASK-006-06 Implement tile/realtime/API failure states without hiding textual member status.
- [ ] TASK-006-07 Add freshness, late-event, paused, reconnect, tile failure and consent-regression tests.
- [ ] TASK-006-08 Publish map-provider privacy/operator documentation and Task → Code/Test graph metadata.
- [ ] TASK-006-09 Add Engineering Graph validation evidence to the implementing PR.

## Initial waves

```text
Wave 1
├── TASK-006-01 map engine
└── TASK-006-02 typed state

Wave 2
├── TASK-006-03 UI
└── TASK-006-04 snapshot/realtime

Wave 3
├── TASK-006-05 cache
└── TASK-006-06 failure states

Wave 4
└── TASK-006-07 tests

Wave 5
└── TASK-006-08 docs + graph

Wave 6
└── TASK-006-09 evidence
```
