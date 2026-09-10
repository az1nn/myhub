---
id: ADR-012
type: adr
status: accepted
---

# ADR-012 — Capability-oriented authorization

## Decision

Initial roles map to capabilities, with backend policy enforcement as authority.

## Rationale

This avoids encoding family labels such as father/mother/child as security roles and supports finer authorization evolution.
