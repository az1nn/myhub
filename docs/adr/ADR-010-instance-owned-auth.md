---
id: ADR-010
type: adr
status: accepted
---

# ADR-010 — Instance-owned authentication

## Decision

Authentication is owned by the MyHub instance. External identity providers are optional.

## Rationale

A family must be able to operate MyHub without mandatory Google, Auth0, Cognito or equivalent dependencies.
