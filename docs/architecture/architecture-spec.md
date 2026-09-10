---
id: DOC-ARCH-001
type: architecture-spec
status: active
constrained_by:
  - ADR-001
  - ADR-002
  - ADR-003
  - ADR-004
  - ADR-005
  - ADR-006
  - ADR-007
  - ADR-008
  - ADR-009
  - ADR-010
  - ADR-011
  - ADR-012
  - ADR-013
  - ADR-014
  - ADR-015
  - ADR-016
  - ADR-017
  - ADR-018
  - ADR-019
---

# MyHub Architecture Spec

## System shape

MyHub is an Android-first, self-hosted family coordination system.

Business runtime:

```text
Internet
  -> Caddy
  -> FastAPI modular monolith
  -> PostgreSQL
  -> worker process
```

Clients:

```text
React Native + Expo + TypeScript
Web client (scope still open)
```

Engineering runtime:

```text
Git repository
  -> Spec Kit
  -> Graph Sync
  -> Neo4j Engineering Graph
  -> CI / impact / drift / context / planning
```

Neo4j is NOT part of the family application's business runtime.

## Deployment topology

Operational default:

```text
Family A -> Instance A
Family B -> Instance B
```

Each deployment normally hosts one family. The domain remains tenant-aware and relevant entities retain `tenant_id`.

## Backend architecture

V0.x uses a modular monolith with modules for identity, families, memberships, invitations, devices, locations, chat, places, reminders, notifications, administration and backups.

Recommended dependency direction:

```text
HTTP/WS adapters
  -> application services
  -> domain
  -> ports
infrastructure adapters -> ports
```

FastAPI route functions SHOULD remain thin.

## Data architecture

Canonical business database: PostgreSQL.

Location separates:

```text
location_history
current_location
```

`location_history` is temporal, retention-controlled event data. `current_location` is a read-optimized projection for map queries.

## Realtime

Transport: WebSocket.

WebSocket is a freshness optimization, not the canonical source of state. Clients MUST be able to rebuild canonical state over HTTP after reconnecting.

Initial event envelope:

```json
{
  "type": "location.current.updated",
  "version": 1,
  "tenant_id": "<uuid>",
  "event_id": "<uuid>",
  "occurred_at": "<timestamp>",
  "data": {}
}
```

## Authentication and authorization

Authentication is instance-owned. Passkeys/WebAuthn are preferred; password is fallback. Social OAuth may exist later but MUST NOT be required.

Initial roles are Owner, Adult and Member. Roles map to capabilities. Backend authorization is authoritative.

## Devices

A user can own multiple devices. One device may be designated as the active location source. Revocation invalidates that device and does not implicitly transfer identity to another device.

## Location pipeline

```text
Android OS location provider
  -> collector
  -> durable local queue
  -> sync worker
  -> FastAPI ingestion
  -> current_location projection
  -> location_history
  -> WebSocket updates
  -> family clients
```

Location event IDs SHOULD be generated before local queuing to support idempotent retries.

## Places and geofencing

Places represent family-relevant geographic areas. Geofence evaluation produces events such as `entered_place` and `left_place`. Events SHOULD feed a timeline/automation layer rather than automatically polluting chat.

## Push

Core domain produces notification intent. Provider delivery is behind a port. Exact FCM dependency remains open.

## Self-hosting

Docker Compose is canonical. Caddy is the default ingress/TLS direction. OpenTofu is optional. Coolify may be supported but is not structural.

## Backup/restore

Portable archive concept:

```text
myhub-backup.tar.gz
├── database.sql.gz
├── attachments/
├── config.json
└── manifest.json
```

Encryption and compatibility details remain open.

## Engineering control plane

MyHub is Spec-Driven and Graph-Driven from repository inception.

Canonical engineering truth:

```text
Markdown/YAML
code
tests
Git metadata
PR metadata
```

Derived graph nodes:

```text
Requirement
Spec
ADR
Task
CodeArtifact
Test
PullRequest
```

Neo4j failure MUST NOT affect production availability.

## Architecture constraints

Do not introduce without demonstrated need and ADR: production Neo4j, Kubernetes, service mesh, distributed brokers, microservices, mandatory central SaaS, mandatory external identity provider, GraphRAG, or AI-inferred canonical engineering relationships.
