---
id: SPEC-003-FAMILY-MEMBERSHIP
type: spec
status: active
requires:
  - REQ-MEMBER-001
  - REQ-MEMBER-002
  - REQ-MEMBER-003
  - REQ-MEMBER-004
  - REQ-MEMBER-005
  - REQ-MEMBER-006
  - REQ-MEMBER-007
  - REQ-MEMBER-008
  - REQ-MEMBER-009
  - REQ-MEMBER-010
critical_requirements:
  - REQ-MEMBER-001
  - REQ-MEMBER-002
  - REQ-MEMBER-004
  - REQ-MEMBER-005
  - REQ-MEMBER-006
  - REQ-MEMBER-008
constrained_by:
  - ADR-001
  - ADR-002
  - ADR-007
  - ADR-008
  - ADR-010
  - ADR-012
  - ADR-015
  - ADR-018
  - ADR-019
depends_on:
  - SPEC-002-AUTHENTICATION
---

# Feature Specification: Family Membership & Invitations

## Problem

A MyHub Owner needs a simple and safe way to bring family members into a self-hosted instance without central account infrastructure, reusable permanent invitation secrets or ambiguous tenant membership.

## Baseline

The approved architecture establishes:

- one family/tenant per deployment as the operational default;
- tenant-aware domain records;
- initial roles `Owner`, `Adult`, `Member`;
- authorization evolves toward capabilities and remains backend-authoritative;
- family invitations use short-lived QR/link tokens;
- invitations are temporary, revocable and one-use when appropriate;
- a mobile client discovers/configures the target instance dynamically.

## Requirements

### REQ-MEMBER-001 — Explicit membership boundary

A user's access to family data MUST be represented by an explicit `Membership` bound to both `tenant_id` and `user_id`.

Authentication alone MUST NOT imply family membership or authorization.

### REQ-MEMBER-002 — Capability-protected invitation creation

Only an authenticated membership with `members.invite` capability may create an invitation.

The backend MUST decide authorization; hiding invitation UI is not sufficient.

### REQ-MEMBER-003 — V0.1 invitation policy

V0.1 invitations are single-use, short-lived and revocable.

An invitation has an explicit intended role of `Adult` or `Member`. `Owner` MUST NOT be assignable through the normal invitation path.

The exact default TTL is configurable and documented by implementation; indefinite invitations are forbidden.

### REQ-MEMBER-004 — Secret handling

The raw invitation token MUST be generated from a cryptographically secure source and returned only when the invitation is created.

The server MUST persist only a verifier/hash sufficient to validate later presentation. Raw invitation tokens MUST NOT appear in logs, audit events or normal database fields.

### REQ-MEMBER-005 — Atomic single-use acceptance

Acceptance MUST atomically ensure that a valid invitation is consumed at most once and that no duplicate active membership is created by concurrent requests.

Expired, revoked, already-consumed and invalid invitations fail closed.

### REQ-MEMBER-006 — Scoped onboarding authority

An invitation token authorizes only the onboarding actions required to establish the invited member. It MUST NOT behave as a general family session or administrative credential.

For a new user, the invitation may authorize credential enrollment through SPEC-002. A normal authenticated session is created only after the new credential is successfully verified.

### REQ-MEMBER-007 — Minimal invitation disclosure

Before acceptance, an invitation preview MAY expose only the minimum information needed for a person to confirm that they are joining the intended instance/family, such as family display name, instance identity/public metadata, intended role and expiration.

It MUST NOT expose the family member list, locations, chat, private settings or other family data.

### REQ-MEMBER-008 — Tenant and role invariants

All membership reads/writes MUST be tenant-scoped.

Initial roles remain:

```text
Owner
Adult
Member
```

Family relationship labels such as parent, child, spouse or sibling are profile metadata and MUST NOT silently become authorization roles.

Child-specific policy remains an open product decision; `Member` MUST NOT be assumed to mean child.

### REQ-MEMBER-009 — Membership removal

A membership with the required capability may remove another removable membership. Removal MUST immediately prevent subsequent authorization to tenant resources even if an authentication session itself remains structurally valid.

Normal membership removal MUST NOT remove the last Owner. Owner transfer/recovery is outside this spec.

### REQ-MEMBER-010 — Instance-aware invitation payload

The invitation artifact must give the mobile client enough information to locate the target self-hosted instance without compiling the app against a central API.

Canonical conceptual payload remains:

```json
{
  "server": "https://family.example.com",
  "invite": "<short-lived-token>"
}
```

The final QR/deep-link encoding MUST avoid unnecessary token exposure to browser history, referrers and server access logs. Exact link encoding is an implementation decision and must be documented before release.

## User story — Owner invites a family member

As an Owner, I want to generate a temporary invitation for a family member so they can join the correct self-hosted instance without me creating a password for them.

Acceptance criteria:

- capability is checked server-side;
- invitation has role, expiry and one-use semantics;
- raw token is shown only at creation;
- QR/link can be shared out of band;
- invitation can be revoked before use.

## User story — New member joins

As an invited family member, I want to open the invitation, verify which family/instance I am joining and establish my own authentication credential.

Acceptance criteria:

- preview reveals only minimal instance/family information;
- expired/revoked/consumed invite is rejected;
- new credential enrollment is bound to the invitation onboarding context;
- user + membership are created transactionally with invite consumption where practical;
- successful credential verification yields a normal session;
- invitation cannot be used again.

## User story — Remove membership

As an authorized family administrator, I want to remove a member so their existing session no longer gives access to family resources.

Acceptance criteria:

- capability is checked;
- removal is tenant-scoped;
- protected resource access fails immediately after membership removal;
- last Owner cannot be removed by this flow.

## Authorization

Candidate capabilities used by this feature:

```text
members.read
members.invite
members.remove
```

Role-to-capability mapping belongs to the authorization policy layer and may evolve without changing the membership entity shape.

## Failure states

Invalid token, expired token, revoked token, consumed token, concurrent acceptance, invalid intended role, duplicate membership, credential enrollment failure, database failure, member removal without capability, last-Owner removal attempt, instance identity mismatch reported by client.

## Security/privacy constraints

- no invitation token in logs;
- no stealth joining or silent membership creation;
- invitation preview is data-minimal;
- tenant boundary applies to every membership query;
- invitation cannot activate location sharing;
- joining a family does not implicitly grant `locations.share` consent;
- membership removal and authentication session validity are distinct; authorization checks membership state.

## Non-goals

- Owner transfer;
- Owner recovery;
- child/guardian-specific controls;
- multiple family groups inside one deployment;
- reusable/bulk invitation links;
- contact discovery;
- email/SMS delivery service run by MyHub;
- device registration, which is SPEC-004;
- final server-identity protocol, which remains an explicit security decision.

## Success criterion

An authorized Owner can issue and revoke a safe single-use invitation, and a new person can use it to establish their own credential and one tenant-scoped family membership without central identity infrastructure or reusable invitation secrets.
