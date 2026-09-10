.PHONY: help spec-init graph-up graph-down graph-sync graph-validate engineering-check

SPECKIT_INTEGRATION ?= opencode

help:
	@echo "spec-init          Initialize/refresh official Spec Kit assets"
	@echo "graph-up           Start local Neo4j engineering graph"
	@echo "graph-down         Stop local Neo4j engineering graph"
	@echo "graph-sync         Synchronize repository artifacts into graph"
	@echo "graph-validate     Validate engineering graph invariants"
	@echo "engineering-check  Run sync + validation"

spec-init:
	./scripts/bootstrap-spec-kit.sh $(SPECKIT_INTEGRATION)

graph-up:
	./scripts/graph-up.sh

graph-down:
	docker compose -f engineering-graph/docker-compose.yml down

graph-sync:
	./scripts/graph-sync.sh

graph-validate:
	./scripts/graph-validate.sh

engineering-check: graph-sync graph-validate
