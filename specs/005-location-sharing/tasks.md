---
id: TASKSET-005-LOCATION-SHARING
type: tasks
status: active
spec_id: SPEC-005-LOCATION-SHARING
depends_on:
  - PLAN-005-LOCATION-SHARING
task_metadata:
  TASK-005-01:
    priority: 1
    depends_on: []
  TASK-005-02:
    priority: 1
    depends_on: []
  TASK-005-03:
    priority: 1
    depends_on: []
  TASK-005-04:
    priority: 2
    depends_on: [TASK-005-01]
  TASK-005-05:
    priority: 2
    depends_on: [TASK-005-02]
  TASK-005-06:
    priority: 2
    depends_on: [TASK-005-02, TASK-005-03]
  TASK-005-07:
    priority: 3
    depends_on: [TASK-005-04, TASK-005-05]
  TASK-005-08:
    priority: 3
    depends_on: [TASK-005-05, TASK-005-06]
  TASK-005-09:
    priority: 3
    depends_on: [TASK-005-04, TASK-005-06]
  TASK-005-10:
    priority: 4
    depends_on: [TASK-005-07, TASK-005-08]
  TASK-005-11:
    priority: 4
    depends_on: [TASK-005-08, TASK-005-09]
  TASK-005-12:
    priority: 4
    depends_on: [TASK-005-01]
  TASK-005-13:
    priority: 5
    depends_on: [TASK-005-10, TASK-005-11, TASK-005-12]
  TASK-005-14:
    priority: 5
    depends_on: [TASK-005-10, TASK-005-11]
  TASK-005-15:
    priority: 6
    depends_on: [TASK-005-13, TASK-005-14]
  TASK-005-16:
    priority: 7
    depends_on: [TASK-005-15]
---

# Tasks: Location Sharing

- [ ] TASK-005-01 Execute/instrument mandatory Android background-location spike and record real-device results.
- [ ] TASK-005-02 Add server location-sharing/event/current-location persistence and migration.
- [ ] TASK-005-03 Implement mobile durable location queue with stable client event IDs.
- [ ] TASK-005-04 Implement Android permission/sharing-state machine and background collector harness.
- [ ] TASK-005-05 Implement device-scoped idempotent batch ingestion and validation.
- [ ] TASK-005-06 Implement current-location projection ordered by accepted `captured_at`, including future-skew protection.
- [ ] TASK-005-07 Implement offline sync/retry/drain worker and permanent-vs-retryable result handling.
- [ ] TASK-005-08 Implement server/mobile PAUSED enforcement and local unsent-queue purge policy.
- [ ] TASK-005-09 Implement centralized freshness/quality semantic policy without freezing unmeasured thresholds.
- [ ] TASK-005-10 Add backend ingestion/idempotency/late-event/tenant/source/paused tests.
- [ ] TASK-005-11 Add mobile permission/queue/retry/pause/source tests using development build where required.
- [ ] TASK-005-12 Convert spike results into initial sampling/battery profiles and update spec/plan if empirical evidence contradicts hypotheses.
- [ ] TASK-005-13 Implement privacy-safe location diagnostics/metrics and failure reason reporting.
- [ ] TASK-005-14 Publish location HTTP contracts, mobile behavior docs and operational troubleshooting.
- [ ] TASK-005-15 Sync final Task → Code/Test relationships and run graph impact/drift/conflict analysis.
- [ ] TASK-005-16 Add Engineering Graph validation evidence to the implementing PR.

## Initial execution waves

```text
Wave 1
├── TASK-005-01 Android spike
├── TASK-005-02 server persistence
└── TASK-005-03 local queue

Wave 2
├── TASK-005-04 collector/permissions
├── TASK-005-05 ingestion
└── TASK-005-06 current projection

Wave 3
├── TASK-005-07 sync worker
├── TASK-005-08 pause enforcement
└── TASK-005-09 freshness semantics

Wave 4
├── TASK-005-10 backend tests
├── TASK-005-11 mobile tests
└── TASK-005-12 evidence-based sampling profiles

Wave 5
├── TASK-005-13 diagnostics
└── TASK-005-14 contracts/docs

Wave 6
└── TASK-005-15 graph reconciliation

Wave 7
└── TASK-005-16 graph evidence
```

The Engineering Graph must recalculate actual READY/conflicts before multi-agent implementation. The Android spike may change downstream dependencies.
