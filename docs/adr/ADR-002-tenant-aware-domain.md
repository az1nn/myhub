---
id: ADR-002
type: adr
status: accepted
---

# ADR-002 — Tenant-aware domain model

## Decision

Relevant domain records retain an explicit family/tenant relationship even though deployments are single-tenant by default.

## Rationale

This preserves isolation, testability, import/export boundaries and future multi-group evolution without coupling the model to one hard-coded family.
