---
id: SPEC-000-ENGINEERING-GRAPH-V1
type: spec
status: active
requires:
  - REQ-GRAPH-001
  - REQ-GRAPH-002
  - REQ-GRAPH-003
  - REQ-GRAPH-004
  - REQ-GRAPH-005
critical_requirements:
  - REQ-GRAPH-003
  - REQ-GRAPH-004
constrained_by:
  - ADR-016
  - ADR-017
  - ADR-018
  - ADR-019
---

# Feature Specification: Engineering Graph V1

## Goal

Create the first usable Engineering Graph control plane from canonical repository artifacts without making Neo4j a source of truth or production dependency.

## Requirements

### REQ-GRAPH-001 — Deterministic repository model

Graph Sync MUST parse explicit repository metadata and build a deterministic in-memory graph.

### REQ-GRAPH-002 — Core traceability

The graph MUST support Requirement, Spec, ADR, Task, CodeArtifact, Test and PullRequest nodes plus the baseline relationships defined by ADR-017.

### REQ-GRAPH-003 — Neo4j synchronization

The current repository graph MUST be reproducibly synchronized into Neo4j. Neo4j remains disposable/derived.

### REQ-GRAPH-004 — Validation gates

Validation MUST detect at least active specs without tasks, done tasks without implementation, missing declared artifacts, critical requirements without tests, unknown task dependencies, task cycles and PRs without task traceability.

### REQ-GRAPH-005 — Pull Request traceability

On GitHub Actions pull-request events, Graph Sync MUST create a PullRequest node, detect explicit `TASK-*` references from PR title/body/branch, and record changed repository artifacts.

## Non-goals

GraphRAG, embeddings, AST-wide inference, AI-generated canonical relationships, distributed scheduling and production business data in Neo4j.
