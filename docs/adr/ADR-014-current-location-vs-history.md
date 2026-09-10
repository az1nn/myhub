---
id: ADR-014
type: adr
status: accepted
---

# ADR-014 — Current location separated from history

## Decision

Current location is a read-optimized projection distinct from retention-controlled temporal location history.

## Rationale

This makes map reads efficient and prevents arrival time/history semantics from being confused with freshness.
