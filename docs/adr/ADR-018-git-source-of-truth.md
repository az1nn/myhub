---
id: ADR-018
type: adr
status: accepted
---

# ADR-018 — Git/repository artifacts remain source of truth

## Decision

Markdown/YAML, code, tests, Git history and PR metadata are canonical. Neo4j is rebuilt from repository evidence.

## Rationale

This avoids split-brain project knowledge and keeps the Engineering Graph disposable and reconstructable.
