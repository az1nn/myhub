---
id: PLAN-000-ENGINEERING-GRAPH-V1
type: plan
status: active
depends_on:
  - SPEC-000-ENGINEERING-GRAPH-V1
---

# Implementation Plan: Engineering Graph V1

## Components

```text
sync/model.py        in-memory graph
sync/common.py       Markdown/frontmatter parsing
sync/specs.py        Spec + Requirement + ADR edges
sync/adrs.py         ADR nodes
sync/tasks.py        Task DAG + code/test evidence
sync/git.py          current PR metadata/change edges
sync/store.py        Neo4j rebuild
sync/sync.py         orchestration
validate/            invariant gate
tests/               parser/model/invariant coverage
```

## Synchronization strategy

V1 uses deterministic rebuild-from-repository semantics:

```text
repository -> GraphModel -> Neo4j rebuild
```

This is acceptable because Neo4j is derived, not canonical. Incremental sync can follow only after V1 proves value.

## Metadata rule

Relationships come from explicit frontmatter, task metadata and Git metadata. V1 does not infer canonical relationships with an LLM.

## CI

CI installs the graph package, runs tests, starts ephemeral Neo4j, performs sync, then validates the repository graph.
