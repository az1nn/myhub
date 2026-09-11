---
id: TASKSET-000-ENGINEERING-GRAPH-V1
type: tasks
status: active
spec_id: SPEC-000-ENGINEERING-GRAPH-V1
task_metadata:
  TASK-ENG-001:
    status: done
    implements:
      - engineering-graph/sync/model.py
    validated_by:
      - engineering-graph/tests/test_model.py
  TASK-ENG-002:
    status: done
    depends_on: [TASK-ENG-001]
    implements:
      - engineering-graph/sync/common.py
      - engineering-graph/sync/specs.py
      - engineering-graph/sync/adrs.py
      - engineering-graph/sync/tasks.py
      - engineering-graph/sync/code.py
    validated_by:
      - engineering-graph/tests/test_parsers.py
  TASK-ENG-003:
    status: done
    depends_on: [TASK-ENG-001, TASK-ENG-002]
    implements:
      - engineering-graph/sync/store.py
      - engineering-graph/sync/sync.py
    validated_by:
      - engineering-graph/tests/test_parsers.py
  TASK-ENG-004:
    status: done
    depends_on: [TASK-ENG-001, TASK-ENG-002]
    implements:
      - engineering-graph/validate/invariants.py
      - engineering-graph/validate/validate.py
    validated_by:
      - engineering-graph/tests/test_invariants.py
  TASK-ENG-005:
    status: done
    depends_on: [TASK-ENG-001]
    implements:
      - engineering-graph/sync/git.py
    validated_by:
      - engineering-graph/tests/test_parsers.py
  TASK-ENG-006:
    status: done
    depends_on: [TASK-ENG-003, TASK-ENG-004, TASK-ENG-005]
    implements:
      - .github/workflows/engineering-graph.yml
    validated_by:
      - engineering-graph/tests/test_model.py
      - engineering-graph/tests/test_parsers.py
      - engineering-graph/tests/test_invariants.py
  TASK-ENG-007:
    status: done
    depends_on: [TASK-ENG-004, TASK-ENG-005]
    implements:
      - engineering-graph/validate/invariants.py
    validated_by:
      - engineering-graph/tests/test_invariants.py
---

# Tasks: Engineering Graph V1

- [x] TASK-ENG-001 Implement in-memory graph model.
- [x] TASK-ENG-002 Parse explicit Spec/ADR/Task/code/test metadata.
- [x] TASK-ENG-003 Synchronize deterministic graph into Neo4j.
- [x] TASK-ENG-004 Implement graph invariant validation and DAG cycle detection.
- [x] TASK-ENG-005 Capture GitHub PR traceability and changed artifacts.
- [x] TASK-ENG-006 Wire tests, Neo4j sync and validation into CI.
- [x] TASK-ENG-007 Make Architecture Gate lifecycle-aware for incremental specs and planning-only PRs.
