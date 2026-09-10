---
id: SPEC-001-INSTANCE-BOOTSTRAP
type: spec
status: active
requires:
  - REQ-BOOT-001
  - REQ-BOOT-002
  - REQ-BOOT-003
  - REQ-BOOT-004
constrained_by:
  - ADR-001
  - ADR-003
  - ADR-004
  - ADR-006
  - ADR-010
  - ADR-018
  - ADR-019
---

# Feature Specification: Instance Bootstrap

## Problem

A fresh self-hosted deployment needs a safe transition from empty installation to usable family instance without default credentials or a centrally operated service.

## Requirements

### REQ-BOOT-001 — Explicit lifecycle

The server MUST expose:

```text
UNINITIALIZED -> BOOTSTRAPPING -> READY
```

A fresh deployment starts `UNINITIALIZED`.

### REQ-BOOT-002 — Initial Owner

Bootstrap MUST create exactly one initial Owner membership before the instance becomes `READY`. No default admin password or hidden account is allowed.

### REQ-BOOT-003 — Required configuration

Bootstrap establishes at least family name, canonical/base URL, instance identity material, initial Owner identity, required secrets and database migration readiness.

### REQ-BOOT-004 — Safe repeat behavior

A `READY` instance MUST reject first-time bootstrap attempts unless a future explicit recovery mechanism authorizes them.

## User story — start a family instance

As the person self-hosting MyHub, I want a fresh deployment to guide creation of the family and first Owner so there are no insecure default credentials.

Acceptance criteria:

- fresh instance reports `UNINITIALIZED`;
- bootstrap can begin safely;
- exactly one initial Owner is created;
- migrations/configuration succeed before READY;
- subsequent first-bootstrap attempts are rejected.

## User story — failed bootstrap

As the operator, I want failed bootstrap to fail visibly and safely rather than leaving the instance falsely ready.

Acceptance criteria:

- partial failure does not report READY;
- errors use stable code/request ID;
- retry semantics are defined;
- secrets are not leaked.

## Authorization

Before READY, bootstrap uses a dedicated bootstrap authorization mechanism defined in the implementation plan. After READY, first-time bootstrap endpoints are disabled/rejected.

## Security constraints

No shipped default password; no bootstrap token in source control; generated secrets are not returned unnecessarily; actions are auditable locally; family identity and Owner membership are created atomically where feasible.

## Failure states

Invalid configuration, database unavailable, migration failure, identity generation failure, Owner creation failure, concurrent bootstrap and re-bootstrap after READY.

## Non-goals

Account recovery, Owner recovery after normal operation, multi-family provisioning in one deployment, central cloud orchestration and production OpenTofu automation.

## Success criterion

A fresh self-hosted deployment can become a secure READY instance with one Owner and no default credentials.
