---
id: DOC-NFR-001
type: nfr
status: active
---

# MyHub Non-Functional Requirements

## Priority order

1. Privacy
2. Location reliability
3. Battery efficiency
4. Operational simplicity
5. Self-hosting usability
6. Security
7. Offline behavior
8. Portability
9. Maintainability
10. Extensibility

Massive scale is not an initial objective.

## Privacy

- Location sharing MUST be explicit, visible and revocable by the sharing user.
- No stealth tracking is allowed.
- Paused sharing MUST NOT be remotely reactivated.
- Retention MUST be finite and configurable.
- Expired location data MUST be purgeable.
- Mandatory external telemetry is prohibited.
- Logs SHOULD avoid precise coordinates and message contents by default.

## Reliability

- Location collection MUST survive temporary network loss through a durable local queue.
- Location ingestion MUST be idempotent.
- Realtime loss MUST be recoverable through canonical HTTP reads.
- Stale or delayed data MUST remain distinguishable from current data.
- Device revocation MUST take effect server-side.

## Battery

- Production background-location policy MUST be empirically validated on real Android devices.
- Fixed aggressive GPS polling is prohibited as a default.
- Sampling SHOULD adapt to movement and active-follow state.
- Battery impact MUST be measured by the required Android spike.

## Operability

Canonical self-hosting remains Docker Compose. The system MUST provide health/readiness, deterministic migrations, documented upgrades, documented backup/restore and useful local logs. Kubernetes, brokers and service mesh are not required.

## Security

Every protected operation MUST evaluate authenticated identity, active membership, tenant boundary, capability and resource-specific rules. Invitations expire and are revocable. Devices have explicit identities and revocation semantics.

## Offline behavior

For location:

```text
capture -> durable local queue -> retry -> idempotent API ingestion
```

`captured_at` MUST be preserved. A feature spec MUST define offline behavior whenever it is materially relevant.

## Portability

Backups MUST be versioned and integrity-checked. Core runtime SHOULD remain provider-independent. A family SHOULD be able to migrate between hosts without reconstructing domain state manually.

## Maintainability

V0.x uses a modular monolith. Domain rules SHOULD not live directly in FastAPI route functions. Cross-client contracts SHOULD be explicit and versioned. Material implementation MUST trace through Spec Kit tasks and Engineering Graph relationships.

## Engineering quality gates

Material PRs run applicable format, lint, typecheck, unit/integration/contract tests, migration checks, container build, dependency/security scans, Graph Sync, graph invariant validation, drift checks and impact analysis.

## Empirical gate

No final production sampling interval or background-tracking policy is accepted until the Android background-location spike produces evidence across relevant OS states and representative devices.
