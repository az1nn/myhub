# MyHub Constitution

**Version:** 1.0.0  
**Status:** Initial governing baseline

## I. Privacy and Consent Are Product Invariants

Location sharing MUST be explicit, visible and revocable by the sharing user.
MyHub MUST NOT implement stealth tracking or remote silent reactivation.
Stale or delayed location MUST NOT be represented as current.

## II. Specification Precedes Material Implementation

Material product work MUST flow through Spec Kit.
The intended lifecycle is constitution → specify → clarify → plan → checklist →
tasks → analyze → implement → converge.

Code MUST NOT silently become the only record of a changed requirement.

## III. Git and Repository Artifacts Are the Source of Truth

Markdown, structured metadata, code, tests, contracts, ADRs and Git history are
canonical. Neo4j is a derived engineering projection.

Agents MUST NOT write canonical project knowledge directly into Neo4j.

## IV. Engineering Graph Traceability Is Mandatory

The Engineering Graph MUST trace Requirements, Specs, ADRs, Tasks,
CodeArtifacts, Tests and PullRequests.

A material Pull Request MUST trace to at least one Task, and that Task MUST
trace to an approved Spec/requirement context.

## V. Backend Authorization and Tenant Isolation Are Mandatory

The backend is the authorization authority.
Relevant persisted domain records MUST preserve tenant/family scope.
Frontend visibility MUST NOT be treated as authorization.

## VI. Offline and Freshness Semantics Are First-Class

Offline location collection and retry behavior MUST be designed explicitly.
`captured_at` and `received_at` MUST remain distinct.
Delayed synchronization MUST NOT create false freshness.

## VII. Self-Hosting and Operational Simplicity Win by Default

Docker Compose is the canonical business runtime.
Infrastructure MUST NOT be added without a demonstrated requirement.
Neo4j belongs to the engineering toolchain, not the MyHub family runtime.

## VIII. Background Location Requires Empirical Evidence

Production sampling, battery policy and Android background behavior MUST be
informed by the required Android background-location spike and real-device
validation, not assumptions alone.

## IX. Contracts, Tests and Observability Are Part of the Feature

Specs MUST define authorization, failure states, privacy/security implications,
offline behavior and retention when relevant.
Cross-client contracts MUST be explicit.
Critical requirements MUST have validation evidence.

## X. Graph Validation Is an Architecture Gate

CI MUST synchronize and validate governed graph invariants.
Task dependency cycles, invalid graph references, critical unvalidated
requirements and completed tasks without implementation evidence are merge
blockers.

## Governance

Changes to these principles require:
1. an explicit constitution amendment;
2. impact analysis;
3. any required superseding ADR;
4. graph synchronization;
5. graph validation.

Feature-level convenience does not override this constitution.
