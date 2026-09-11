from __future__ import annotations

from pathlib import Path

from .model import GraphModel


def sync_known_artifacts(repo_root: Path, graph: GraphModel) -> None:
    """Refresh existence metadata for artifacts referenced explicitly by tasks."""
    for node in list(graph.nodes.values()):
        if node.ref.label not in {"CodeArtifact", "Test"}:
            continue
        path = repo_root / str(node.ref.key_value)
        node.properties["exists"] = path.exists()
