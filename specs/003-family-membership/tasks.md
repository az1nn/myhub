---
id: TASKSET-003-FAMILY-MEMBERSHIP
type: tasks
status: active
spec_id: SPEC-003-FAMILY-MEMBERSHIP
depends_on:
  - PLAN-003-FAMILY-MEMBERSHIP
task_metadata:
  TASK-003-01:
    priority: 1
    depends_on: []
  TASK-003-02:
    priority: 1
    depends_on: []
  TASK-003-03:
    priority: 2
    depends_on: [TASK-003-01, TASK-003-02]
  TASK-003-04:
    priority: 2
    depends_on: [TASK-003-01]
  TASK-003-05:
    priority: 3
    depends_on: [TASK-003-03]
  TASK-003-06:
    priority: 3
    depends_on: [TASK-003-03]
  TASK-003-07:
    priority: 3
    depends_on: [TASK-003-03]
  TASK-003-08:
    priority: 4
    depends_on: [TASK-003-05, TASK-003-06]
  TASK-003-09:
    priority: 4
    depends_on: [TASK-003-05, TASK-003-07]
  TASK-003-10:
    priority: 4
    depends_on: [TASK-003-02]
  TASK-003-11:
    priority: 5
    depends_on: [TASK-003-08, TASK-003-09, TASK-003-10]
  TASK-003-12:
    priority: 5
    depends_on: [TASK-003-08, TASK-003-09]
  TASK-003-13:
    priority: 6
    depends_on: [TASK-003-11, TASK-003-12]
  TASK-003-14:
    priority: 7
    depends_on: [TASK-003-13]
---

# Tasks: Family Membership & Invitations

- [ ] TASK-003-01 Add invitation persistence model/migration with expiry, revocation and one-use state.
- [ ] TASK-003-02 Centralize initial role-to-capability policy for `Owner`, `Adult`, `Member` and membership-state authorization checks.
- [ ] TASK-003-03 Implement secure invitation token generation, hashing, lookup and constant-time verification.
- [ ] TASK-003-04 Implement tenant-scoped membership repository invariants and duplicate-membership protection.
- [ ] TASK-003-05 Implement capability-protected invitation creation and revocation.
- [ ] TASK-003-06 Implement minimal invitation preview/validation without family-data disclosure.
- [ ] TASK-003-07 Implement short-lived invitation onboarding context integrated with SPEC-002 credential enrollment.
- [ ] TASK-003-08 Implement atomic invitation acceptance + User/Membership/credential/session establishment.
- [ ] TASK-003-09 Implement concurrent single-use protection and safe retry semantics.
- [ ] TASK-003-10 Implement membership removal with last-Owner protection and immediate authorization-state effect.
- [ ] TASK-003-11 Add creation/expiry/revocation/acceptance/concurrency/role integration tests.
- [ ] TASK-003-12 Add tenant isolation, removal, last-Owner and no-location-consent regression tests.
- [ ] TASK-003-13 Publish invitation/membership API contracts, QR/deep-link rules and operator docs; sync graph traceability.
- [ ] TASK-003-14 Add Engineering Graph validation evidence to the implementing PR.

## Initial execution waves

```text
Wave 1
├── TASK-003-01 invitation persistence
└── TASK-003-02 capability policy

Wave 2
├── TASK-003-03 token service
└── TASK-003-04 membership invariants

Wave 3
├── TASK-003-05 create/revoke
├── TASK-003-06 preview
├── TASK-003-07 onboarding context
└── TASK-003-10 removal

Wave 4
├── TASK-003-08 acceptance
└── TASK-003-09 concurrency/retry

Wave 5
├── TASK-003-11 lifecycle tests
└── TASK-003-12 isolation/removal tests

Wave 6
└── TASK-003-13 contracts + graph sync

Wave 7
└── TASK-003-14 graph evidence
```

`task_metadata` is canonical; the Engineering Graph recalculates readiness/conflicts before implementation.
