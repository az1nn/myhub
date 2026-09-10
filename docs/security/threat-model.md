---
id: DOC-SEC-001
type: threat-model
status: active
---

# MyHub Threat Model

## High-sensitivity assets

- precise/current/historical location;
- family membership;
- device identities;
- authentication/session material;
- invitation tokens;
- chat messages;
- places such as home/school/work;
- backup archives;
- instance identity/private-key material.

## Trust boundaries

1. Android client <-> MyHub server.
2. Web client <-> MyHub server.
3. Caddy <-> FastAPI.
4. FastAPI <-> PostgreSQL.
5. Worker <-> PostgreSQL/providers.
6. Self-host operator <-> host filesystem/backups.
7. Notification provider boundary.
8. Engineering repository <-> Neo4j Engineering Graph.

Neo4j is not a business-runtime trust dependency.

## Threats

### Stolen/replayed invitation

Controls: short lifetime, server-side revocation, usage limits, minimum exposed preview data, token hashing where practical, and binding to validated instance identity.

### Stolen device

Controls: explicit device identity, server-side revocation, session invalidation and no implicit identity transfer.

### Cross-tenant access

Controls: tenant-scoped data, backend authorization, invariant tests, and never trusting client-supplied tenant identity alone.

### Privilege escalation by family member

Controls: backend role/capability checks, resource-specific policy and audit events for privileged operations.

### Server impersonation

Controls require a dedicated protocol decision: HTTPS, instance identity validation, rotation and recovery semantics.

### Location spoofing/replay

Controls: stable event IDs, captured/received timestamps, device identity, ingestion validation and explicit out-of-order handling. V0.x does not claim strong anti-spoof protection against a fully compromised client device.

### Stale-location confusion

Controls: explicit freshness state, preserved `captured_at`, visible offline/paused/unavailable states and a prohibition on labeling stale coordinates as current.

### WebSocket authorization drift

Controls: authenticated connection, membership/capability checks at relevant boundaries, and disconnection/restriction after revocation.

### Backup exfiltration

Controls: treat archives as sensitive, use minimal filesystem permissions and integrity manifests. Backup encryption is a required decision before the feature ships.

### Malicious/incompatible restore

Controls: versioned manifest, checksums, compatibility validation and validation before destructive restore.

### Owner lockout/recovery abuse

Status: OPEN. Recovery MUST NOT become an easier takeover path than normal authentication.

### Push token leakage

Controls: sensitive handling, device binding, token lifecycle/revocation and no unnecessary logging/exposure.

## Security release blockers

When applicable, these block release: cross-tenant access, bypass of consent-first sharing, remote silent activation, authorization bypass, acceptance of expired/revoked invitations, acceptance of revoked devices, stale location displayed as current, and restore without integrity/compatibility validation.

## Open security decisions

Exact passkey ceremony, account recovery, Owner recovery, server identity, key rotation, encryption at rest, backup encryption and future message E2EE remain open.
