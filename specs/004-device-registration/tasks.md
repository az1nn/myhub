---
id: TASKSET-004-DEVICE-REGISTRATION
type: tasks
status: active
spec_id: SPEC-004-DEVICE-REGISTRATION
depends_on:
  - PLAN-004-DEVICE-REGISTRATION
task_metadata:
  TASK-004-01:
    priority: 1
    depends_on: []
  TASK-004-02:
    priority: 1
    depends_on: []
  TASK-004-03:
    priority: 2
    depends_on: [TASK-004-01, TASK-004-02]
  TASK-004-04:
    priority: 2
    depends_on: [TASK-004-01]
  TASK-004-05:
    priority: 3
    depends_on: [TASK-004-03, TASK-004-04]
  TASK-004-06:
    priority: 3
    depends_on: [TASK-004-03]
  TASK-004-07:
    priority: 3
    depends_on: [TASK-004-03]
  TASK-004-08:
    priority: 4
    depends_on: [TASK-004-05, TASK-004-06, TASK-004-07]
  TASK-004-09:
    priority: 4
    depends_on: [TASK-004-05]
  TASK-004-10:
    priority: 5
    depends_on: [TASK-004-08, TASK-004-09]
  TASK-004-11:
    priority: 6
    depends_on: [TASK-004-10]
---

# Tasks: Device Registration

- [ ] TASK-004-01 Add Device persistence/migration and one-active-location-source invariant.
- [ ] TASK-004-02 Implement scoped device credential issue/verify primitives with secure hashing and one-time disclosure.
- [ ] TASK-004-03 Implement authenticated idempotent device registration and ownership derivation.
- [ ] TASK-004-04 Implement backend device authorization/self-service policy.
- [ ] TASK-004-05 Implement device list/read API with tenant/user scoping.
- [ ] TASK-004-06 Implement atomic location-source selection independent from sharing consent.
- [ ] TASK-004-07 Implement device revocation and device-principal rejection.
- [ ] TASK-004-08 Add registration/source/revocation/tenant-isolation integration tests.
- [ ] TASK-004-09 Add mobile `DeviceCredentialStore` secure-storage adapter contract and tests.
- [ ] TASK-004-10 Publish Device API contract/operator docs and update Task → Code/Test graph metadata.
- [ ] TASK-004-11 Add Engineering Graph validation evidence to the implementing PR.

## Initial execution waves

```text
Wave 1
├── TASK-004-01 persistence
└── TASK-004-02 device credential

Wave 2
├── TASK-004-03 registration
└── TASK-004-04 policy

Wave 3
├── TASK-004-05 listing
├── TASK-004-06 source selection
└── TASK-004-07 revocation

Wave 4
├── TASK-004-08 backend tests
└── TASK-004-09 mobile secure storage

Wave 5
└── TASK-004-10 contracts + graph metadata

Wave 6
└── TASK-004-11 graph evidence
```
