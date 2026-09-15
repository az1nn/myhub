---
id: TASKSET-003-FAMILY-MEMBERSHIP
type: tasks
status: active
spec_id: SPEC-003-FAMILY-MEMBERSHIP
depends_on:
  - PLAN-003-FAMILY-MEMBERSHIP
task_metadata:
  TASK-003-01:
    status: done
    priority: 1
    depends_on: []
    implements:
      - services/api/migrations/versions/0004_membership_invitations.py
      - services/api/src/myhub/infrastructure/db/models.py
    validated_by:
      - services/api/tests/unit/memberships/test_invitation_model.py
  TASK-003-02:
    status: done
    priority: 1
    depends_on: []
    implements:
      - services/api/src/myhub/modules/memberships/policy.py
    validated_by:
      - services/api/tests/unit/memberships/test_policy.py
  TASK-003-03:
    status: done
    priority: 2
    depends_on: [TASK-003-01, TASK-003-02]
    implements:
      - services/api/src/myhub/modules/invitations/tokens.py
    validated_by:
      - services/api/tests/unit/memberships/test_invitation_tokens.py
  TASK-003-04:
    status: done
    priority: 2
    depends_on: [TASK-003-01]
    implements:
      - services/api/src/myhub/modules/memberships/repository.py
    validated_by:
      - services/api/tests/unit/memberships/test_repository.py
  TASK-003-05:
    status: done
    priority: 3
    depends_on: [TASK-003-03]
    implements:
      - services/api/src/myhub/modules/invitations/service.py
    validated_by:
      - services/api/tests/unit/memberships/test_invitation_service.py
  TASK-003-06:
    status: done
    priority: 3
    depends_on: [TASK-003-03]
    implements:
      - services/api/src/myhub/modules/invitations/service.py
    validated_by:
      - services/api/tests/unit/memberships/test_invitation_service.py
  TASK-003-07:
    status: done
    priority: 3
    depends_on: [TASK-003-03]
    implements:
      - services/api/migrations/versions/0005_invitation_onboarding_contexts.py
      - services/api/src/myhub/infrastructure/db/models.py
      - services/api/src/myhub/modules/invitations/onboarding.py
    validated_by:
      - services/api/tests/unit/memberships/test_onboarding_context.py
  TASK-003-08:
    status: done
    priority: 4
    depends_on: [TASK-003-05, TASK-003-06]
    implements:
      - services/api/src/myhub/modules/invitations/acceptance.py
    validated_by:
      - services/api/tests/unit/memberships/test_invitation_acceptance.py
  TASK-003-09:
    status: done
    priority: 4
    depends_on: [TASK-003-05, TASK-003-07]
    implements:
      - services/api/src/myhub/modules/invitations/acceptance.py
    validated_by:
      - services/api/tests/unit/memberships/test_invitation_acceptance.py
  TASK-003-10:
    status: done
    priority: 4
    depends_on: [TASK-003-02]
    implements:
      - services/api/src/myhub/modules/memberships/lifecycle.py
    validated_by:
      - services/api/tests/unit/memberships/test_membership_lifecycle.py
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

- [x] TASK-003-01 Add invitation persistence model/migration with expiry, revocation and one-use state.
- [x] TASK-003-02 Centralize initial role-to-capability policy for `Owner`, `Adult`, `Member` and membership-state authorization checks.
- [x] TASK-003-03 Implement secure invitation token generation, hashing, lookup and constant-time verification.
- [x] TASK-003-04 Implement tenant-scoped membership repository invariants and duplicate-membership protection.
- [x] TASK-003-05 Implement capability-protected invitation creation and revocation.
- [x] TASK-003-06 Implement minimal invitation preview/validation without family-data disclosure.
- [x] TASK-003-07 Implement short-lived invitation onboarding context integrated with SPEC-002 credential enrollment.
- [x] TASK-003-08 Implement atomic invitation acceptance + User/Membership/credential/session establishment.
- [x] TASK-003-09 Implement concurrent single-use protection and safe retry semantics.
- [x] TASK-003-10 Implement membership removal with last-Owner protection and immediate authorization-state effect.
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
