# MyHub

Open-source, self-hosted, privacy-first family coordination.

MyHub is **Spec-Driven and Graph-Driven from day zero**.

## Engineering foundation

```text
Spec Kit
   +
Git source of truth
   +
Neo4j Engineering Graph
```

Neo4j is development/CI infrastructure. It is not part of the MyHub family application runtime.

## Start here

1. `.specify/memory/constitution.md`
2. `docs/product/product-spec.md`
3. `docs/architecture/architecture-spec.md`
4. `docs/engineering/graph-engineering-reference.md`
5. `engineering-graph/README.md`

## Bootstrap

```bash
./scripts/bootstrap-spec-kit.sh opencode
./scripts/graph-up.sh
./scripts/graph-sync.sh
./scripts/graph-validate.sh
```

The first application work must continue through Spec Kit before material implementation.
