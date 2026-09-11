---
id: ADR-017
type: adr
status: accepted
---

# ADR-017 — Neo4j Engineering Graph as derived engineering control plane

## Decision

Neo4j represents engineering traceability, impact, drift and execution context. It is not a MyHub business database.

## Rationale

The graph connects Requirements, Specs, ADRs, Tasks, CodeArtifacts, Tests and PullRequests while keeping production independent of Neo4j.
