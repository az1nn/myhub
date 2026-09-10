# MyHub Engineering Graph

Neo4j is an engineering control-plane component, not a MyHub business database.

## Source of truth

Canonical:

```text
Git repository
├── Spec Kit artifacts
├── ADRs
├── code
├── tests
└── Git / PR metadata
```

Derived:

```text
Graph Sync → Neo4j
```

## V1

Nodes:

```text
Requirement, Spec, ADR, Task, CodeArtifact, Test, PullRequest
```

Queries:

```text
impact
ready
conflicts
drift
context
```

## Local start

```bash
cp engineering-graph/.env.example engineering-graph/.env
docker compose -f engineering-graph/docker-compose.yml up -d
```

## Rules

- never manually author canonical requirements in Neo4j;
- graph edges should come from explicit repository metadata/conventions;
- AI-inferred relationships are out of scope for V1;
- GraphRAG is future work;
- Neo4j failure must not affect MyHub application runtime.
