---
id: ADR-001
type: adr
status: accepted
---

# ADR-001 — Single-tenant deployment as default

## Decision

Each MyHub deployment hosts one family by default.

## Rationale

This matches the initial use case, creates a simple privacy/operational boundary and keeps self-hosting understandable.

## Consequences

Shared multi-tenant infrastructure is not the default. A change requires a superseding ADR and impact analysis.
