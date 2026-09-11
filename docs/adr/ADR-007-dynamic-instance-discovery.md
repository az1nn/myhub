---
id: ADR-007
type: adr
status: accepted
---

# ADR-007 — Client dynamically configures/discovers server

## Decision

Clients bind to a family instance dynamically rather than being compiled against a project-operated fixed API.

## Rationale

Independent self-hosted deployments require the client to know and validate its selected instance.
