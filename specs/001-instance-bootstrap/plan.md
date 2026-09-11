---
id: PLAN-001-INSTANCE-BOOTSTRAP
type: plan
status: active
depends_on:
  - SPEC-001-INSTANCE-BOOTSTRAP
---

# Implementation Plan: Instance Bootstrap

## Approach

Implement bootstrap inside the FastAPI modular monolith using a bootstrap API adapter, application service, family/instance domain creation, Owner creation, instance identity boundary, configuration validator and PostgreSQL transaction.

## State persistence

Persist lifecycle state:

```text
UNINITIALIZED
BOOTSTRAPPING
READY
```

Transitions MUST be safe enough that a crash cannot falsely expose READY.

## Proposed API

```text
GET  /api/v1/instance
POST /api/v1/bootstrap/start
POST /api/v1/bootstrap/complete
```

The implementation may collapse start/complete if security and retry semantics are preserved.

## Concurrency

Use database uniqueness/locking to prevent concurrent creation of multiple initial Owners.

## Required tests

- state-transition unit tests;
- successful first-bootstrap integration test;
- failed-transaction test;
- concurrent-bootstrap test;
- READY re-bootstrap rejection;
- no-default-credential test;
- tenant/Owner invariant test.

## Graph traceability

```text
REQ-BOOT-* -> SPEC-001 -> TASK-001-* -> CodeArtifact/Test -> PR
```

## Risks

The exact initial authentication ceremony depends on SPEC-002 authentication, and the final server-identity protocol is still open. Any temporary bootstrap credential MUST be narrowly scoped and superseded by the authentication spec rather than becoming an accidental permanent mechanism.
