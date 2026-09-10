---
id: TASKSET-001-INSTANCE-BOOTSTRAP
type: tasks
status: active
spec_id: SPEC-001-INSTANCE-BOOTSTRAP
depends_on:
  - PLAN-001-INSTANCE-BOOTSTRAP
task_metadata:
  TASK-001-01:
    priority: 1
    depends_on: []
    validated_by:
      - services/api/tests/unit/bootstrap/test_state_machine.py
  TASK-001-02:
    priority: 2
    depends_on: [TASK-001-01]
  TASK-001-03:
    priority: 1
    depends_on: []
  TASK-001-04:
    priority: 1
    depends_on: []
    validated_by:
      - services/api/tests/integration/bootstrap/test_owner_creation.py
  TASK-001-05:
    priority: 3
    depends_on: [TASK-001-02, TASK-001-03, TASK-001-04]
  TASK-001-06:
    priority: 4
    depends_on: [TASK-001-05]
  TASK-001-07:
    priority: 4
    depends_on: [TASK-001-05]
  TASK-001-08:
    priority: 4
    depends_on: [TASK-001-05]
    validated_by:
      - services/api/tests/integration/bootstrap/test_concurrency.py
  TASK-001-09:
    priority: 5
    depends_on: [TASK-001-01]
    validated_by:
      - services/api/tests/unit/bootstrap/test_state_machine.py
  TASK-001-10:
    priority: 5
    depends_on: [TASK-001-07, TASK-001-08]
    validated_by:
      - services/api/tests/integration/bootstrap/test_bootstrap_api.py
  TASK-001-11:
    priority: 5
    depends_on: [TASK-001-05]
  TASK-001-12:
    priority: 6
    depends_on: [TASK-001-06, TASK-001-07]
  TASK-001-13:
    priority: 7
    depends_on: [TASK-001-09, TASK-001-10, TASK-001-12]
  TASK-001-14:
    priority: 8
    depends_on: [TASK-001-13]
---

# Tasks: Instance Bootstrap

- [ ] TASK-001-01 Define bootstrap state machine and invariants.
- [ ] TASK-001-02 Add persistence model/migration for bootstrap state.
- [ ] TASK-001-03 Implement configuration validation and instance-identity boundary.
- [ ] TASK-001-04 Implement atomic family + initial Owner creation.
- [ ] TASK-001-05 Implement bootstrap application service.
- [ ] TASK-001-06 Implement `GET /api/v1/instance` bootstrap-status response.
- [ ] TASK-001-07 Implement bootstrap mutation endpoint(s).
- [ ] TASK-001-08 Add concurrent-bootstrap protection.
- [ ] TASK-001-09 Add state-transition unit tests.
- [ ] TASK-001-10 Add success/failure/retry/re-bootstrap integration tests.
- [ ] TASK-001-11 Add structured logs/audit events without secret leakage.
- [ ] TASK-001-12 Add detailed API contract and operator docs.
- [ ] TASK-001-13 Sync Requirement/Spec/Task/Code/Test relationships into Engineering Graph.
- [ ] TASK-001-14 Add graph validation evidence to the implementing PR.

## Initial execution waves

```text
Wave 1
├── TASK-001-01
├── TASK-001-03
└── TASK-001-04

Wave 2
├── TASK-001-02
└── TASK-001-09

Wave 3
└── TASK-001-05

Wave 4
├── TASK-001-06
├── TASK-001-07
├── TASK-001-08
└── TASK-001-11

Wave 5
└── TASK-001-10

Wave 6
└── TASK-001-12

Wave 7
└── TASK-001-13

Wave 8
└── TASK-001-14
```

The `task_metadata` block is canonical for machine-readable dependencies. The diagram is only a human-readable projection.
