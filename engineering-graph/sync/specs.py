from __future__ import annotations

from pathlib import Path

from .common import as_list, first_heading, load_markdown
from .model import GraphModel


def sync_specs(repo_root: Path, graph: GraphModel) -> None:
    specs_root = repo_root / "specs"
    if not specs_root.exists():
        return

    for path in sorted(specs_root.rglob("spec.md")):
        meta, body = load_markdown(path)
        spec_id = meta.get("id")
        if not spec_id:
            continue

        spec = graph.upsert_node(
            "Spec", "id", str(spec_id),
            title=first_heading(body),
            status=str(meta.get("status", "active")),
            source_path=path.relative_to(repo_root).as_posix(),
        )

        critical = {str(x) for x in as_list(meta.get("critical_requirements"))}
        for requirement_id in as_list(meta.get("requires")):
            requirement_id = str(requirement_id)
            req = graph.upsert_node(
                "Requirement", "id", requirement_id,
                critical=requirement_id in critical,
                source_path=path.relative_to(repo_root).as_posix(),
            )
            graph.add_edge(req, "REALIZED_BY", spec)

        for adr_id in as_list(meta.get("constrained_by")):
            adr = graph.upsert_node("ADR", "id", str(adr_id))
            graph.add_edge(spec, "CONSTRAINED_BY", adr)

        for dep_id in as_list(meta.get("depends_on")):
            dep = graph.upsert_node("Spec", "id", str(dep_id))
            graph.add_edge(spec, "DEPENDS_ON", dep)
