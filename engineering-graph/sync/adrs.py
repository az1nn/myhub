from __future__ import annotations

from pathlib import Path

from .common import first_heading, load_markdown
from .model import GraphModel


def sync_adrs(repo_root: Path, graph: GraphModel) -> None:
    adr_root = repo_root / "docs" / "adr"
    if not adr_root.exists():
        return

    for path in sorted(adr_root.glob("ADR-*.md")):
        meta, body = load_markdown(path)
        adr_id = meta.get("id")
        if not adr_id:
            continue
        graph.upsert_node(
            "ADR", "id", str(adr_id),
            title=first_heading(body),
            status=str(meta.get("status", "unknown")),
            source_path=path.relative_to(repo_root).as_posix(),
        )
