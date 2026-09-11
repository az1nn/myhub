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
    status: done
    depends_on: []
    implements:
      - services/api/src/myhub/domain/bootstrap.py
    validated_by:
      - services/api/tests/unit/bootstrap/test_state_machine.py
  TASK-001-02:
    priority: 2
    status: done
    depends_on: [TASK-001-01]
    implements:
      - services/api/src/myhub/infrastructure/db/models.py
      - services/api/migrations/versions/0001_instance_bootstrap.py
  TASK-001-03:
    priority: 1
    status: done
    depends_on: []
    implements:
      - services/api/src/myhub/modules/administration/config.py
      - services/api/src/myhub/infrastructure/identity.py
    validated_by:
      - services/api/tests/unit/bootstrap/test_config.py
  TASK-001-04:
    priority: 1
    status: done
    depends_on: []
    implements:
      - services/api/src/myhub/modules/administration/bootstrap_repository.py
    validated_by:
      - services/api/tests/integration/bootstrap/test_owner_creation.py
  TASK-001-05:
    priority: 3
    status: done
    depends_on: [TASK-001-02, TASK-001-03, TASK-001-04]
    implements:
      - services/api/src/myhub/modules/administration/bootstrap_service.py
  TASK-001-06:
    priority: 4
    status: done
    depends_on: [TASK-001-05]
    implements:
      - services/api/src/myhub/app/routes.py
    validated_by:
      - services/api/tests/integration/bootstrap/test_bootstrap_api.py
  TASK-001-07:
    priority: 4
    status: done
    depends_on: [TASK-001-05]
    implements:
      - services/api/src/myhub/app/routes.py
    validated_by:
      - services/api/tests/integration/bootstrap/test_bootstrap_api.py
  TASK-001-08:
    priority: 4
    status: done
    depends_on: [TASK-001-05]
    implements:
      - services/api/src/myhub/modules/administration/bootstrap_repository.py
      - services/api/src/myhub/modules/administration/bootstrap_service.py
    validated_by:
      - services/api/tests/integration/bootstrap/test_concurrency.py
      - services/api/tests/integration/bootstrap/test_postgres_concurrency.py
  TASK-001-09:
    priority: 5
    status: done
    depends_on: [TASK-001-01]
    implements:
      - services/api/src/myhub/domain/bootstrap.py
    validated_by:
      - services/api/tests/unit/bootstrap/test_state_machine.py
  TASK-001-10:
    priority: 5
    status: done
    depends_on: [TASK-001-07, TASK-001-08]
    implements:
      - services/api/src/myhub/app/errors.py
      - services/api/src/myhub/app/routes.py
    validated_by:
      - services/api/tests/integration/bootstrap/test_bootstrap_api.py
  TASK-001-11:
    priority: 5
    status: done
    depends_on: [TASK-001-05]
    implements:
      - services/api/src/myhub/modules/administration/bootstrap_service.py
  TASK-001-12:
    priority: 6
    status: done
    depends_on: [TASK-001-06, TASK-001-07]
    implements:
      - docs/api/instance-bootstrap.md
      - services/api/README.md
  TASK-001-13:
    priority: 7
    status: done
    depends_on: [TASK-001-09, TASK-001-10, TASK-001-12]
    implements:
      - specs/001-instance-bootstrap/tasks.md
  TASK-001-14:
    priority: 8
    status: pending
    depends_on: [TASK-001-13]
---

# Tasks: Instance Bootstrap

- [x] TASK-001-01 Define bootstrap state machine and invariants.
- [x] TASK-001-02 Add persistence model/migration for bootstrap state.
- [x] TASK-001-03 Implement configuration validation and instance-identity boundary.
- [x] TASK-001-04 Implement atomic family + initial Owner creation.
- [x] TASK-001-05 Implement bootstrap application service.
- [x] TASK-001-06 Implement `GET /api/v1/instance` bootstrap-status response.
- [x] TASK-001-07 Implement bootstrap mutation endpoint(s).
- [x] TASK-001-08 Add concurrent-bootstrap protection.
- [x] TASK-001-09 Add state-transition unit tests.
- [x] TASK-001-10 Add success/failure/retry/re-bootstrap integration tests.
- [x] TASK-001-11 Add structured logs/audit events without secret leakage.
- [x] TASK-001-12 Add detailed API contract and operator docs.
- [x] TASK-001-13 Sync Requirement/Spec/Task/Code/Test relationships into Engineering Graph.
- [ ] TASK-001-14 Add graph validation evidence to the implementing PR.

## Execution status

Waves 1 through 7 are implemented in this PR. TASK-001-14 intentionally remains pending until the PR is evaluated by the merged Engineering Graph V1 gate, because validation evidence must come from the actual implementing PR rather than be self-asserted before CI.
