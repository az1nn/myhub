---
id: ADR-011
type: adr
status: accepted
---

# ADR-011 — Passkey-first authentication

## Decision

Passkeys/WebAuthn are preferred. Password is the fallback mechanism.

## Rationale

This reduces password dependence while keeping a viable fallback for self-hosted deployments. Recovery remains a separate open decision.
