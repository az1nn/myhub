from __future__ import annotations

import argparse
import os
from pathlib import Path

from sync.adrs import sync_adrs
from sync.code import sync_known_artifacts
from sync.git import sync_pull_request
from sync.model import GraphModel
from sync.specs import sync_specs
from sync.tasks import sync_tasks


def build_graph(repo_root: Path) -> GraphModel:
    graph = GraphModel()
    sync_adrs(repo_root, graph)
    sync_specs(repo_root, graph)
    sync_tasks(repo_root, graph)
    sync_known_artifacts(repo_root, graph)
    sync_pull_request(repo_root, graph)
    return graph


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and sync the MyHub Engineering Graph")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    graph = build_graph(repo_root)
    print(f"nodes={len(graph.nodes)} edges={len(graph.edges)}")

    if args.dry_run:
        for label in sorted({node.ref.label for node in graph.nodes.values()}):
            count = len([node for node in graph.nodes.values() if node.ref.label == label])
            print(f"{label}={count}")
        return

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "change-me")

    from sync.store import Neo4jStore

    store = Neo4jStore(uri, user, password)
    try:
        store.verify_connectivity()
        store.rebuild(graph)
        print("synced", store.counts())
    finally:
        store.close()


if __name__ == "__main__":
    main()
