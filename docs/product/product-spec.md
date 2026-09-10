---
id: DOC-PRODUCT-001
type: product-spec
status: active
---

# MyHub Product Spec

## Vision

MyHub is an open-source, self-hosted, privacy-first family coordination application.

Its core proposition is:

> where we are + what we need to communicate + what we must not forget.

The project distributes software rather than operating a mandatory central SaaS.

## Primary operating model

The initial target is a small family, approximately four members. The operational default is **one family per deployment**, while the domain remains tenant-aware so relevant records preserve an explicit family/tenant boundary.

## Product principles

1. Family coordination before tracking.
2. Location sharing is explicit, visible and revocable.
3. No stealth mode or remote silent activation.
4. Self-hosting is a first-class capability.
5. Operational simplicity wins over distributed-system complexity.
6. Stale location is never represented as current.
7. Offline behavior is part of the product contract.
8. Backend remains the authorization authority.
9. Material work follows Spec Kit.
10. Git, specs, code and tests are engineering source of truth; Neo4j is a derived Engineering Graph.

## V0.1 — first usable vertical slice

V0.1 MUST support:

- instance bootstrap and initial Owner;
- authentication;
- family membership and invitation;
- device registration;
- explicit location sharing;
- Android background location;
- offline location queue and later synchronization;
- current family map with freshness semantics;
- family chat;
- push notifications.

### Primary journey

1. Owner starts a self-hosted MyHub instance.
2. Owner completes bootstrap.
3. Owner creates a short-lived invitation.
4. Member opens the QR/link.
5. Client validates instance identity and invitation.
6. Member authenticates or creates an identity.
7. Device is registered.
8. Member explicitly enables location sharing.
9. Device publishes permitted background location.
10. Family map shows permitted members with explicit freshness.
11. Members exchange text messages.
12. Relevant activity produces push notifications.

## V0.2

- places;
- geofencing;
- enter/leave events;
- reactions;
- pinned messages;
- basic instance administration.

## V0.3

- location history;
- timeline;
- temporal reminders;
- contextual reminders;
- configurable retention;
- backup/restore.

## Non-goals

MyHub is not a complete Life360 clone, WhatsApp, a social network, employee-surveillance system, MDM, covert tracker, centrally hosted public SaaS, or a Kubernetes/microservice-first platform.

## Roles and authorization

Initial roles:

```text
Owner
Adult
Member
```

Family relationships such as parent, child or sibling are profile attributes, not technical roles. Roles map to backend-enforced capabilities.

## Location semantics

Sharing states:

```text
active
paused
temporary
```

UI MUST distinguish:

```text
fresh
approximate
stale
offline
paused
unavailable
```

`captured_at` and `received_at` remain distinct. A delayed upload MUST NOT become fresh merely because it has just reached the server.

## Open product decisions

The following remain intentionally open until resolved by specs/ADRs: final retention; route visualization; DMs; attachments; reactions/reply/pinning details; push-provider strategy; web-client scope; account and Owner recovery; server identity protocol; encryption at rest; backup encryption; future message E2EE; child-profile rules; final production tracking algorithm.
