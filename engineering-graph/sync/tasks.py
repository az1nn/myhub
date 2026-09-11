from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .common import load_markdown
from .model import GraphModel


TASK_LINE = re.compile(r"^- \[(?P<done>[ xX])\]\s+(?P<id>TASK-[A-Z0-9-]+)\s+(?P<title>.+?)\s*$")


def _task_metadata(meta: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = meta.get("task_metadata") or {}
    if not isinstance(raw, dict):
        raise ValueError("task_metadata must be a mapping")
    return {str(key): (value or {}) for key, value in raw.items()}


def sync_tasks(repo_root: Path, graph: GraphModel) -> None:
    specs_root = repo_root / "specs"
    if not specs_root.exists():
        return

    for path in sorted(specs_root.rglob("tasks.md")):
        meta, body = load_markdown(path)
        metadata = _task_metadata(meta)
        source_path = path.relative_to(repo_root).as_posix()

        parent_spec_id = meta.get("spec_id")
        if not parent_spec_id:
            sibling_spec = path.parent / "spec.md"
            if sibling_spec.exists():
                spec_meta, _ = load_markdown(sibling_spec)
                parent_spec_id = spec_meta.get("id")

        for line in body.splitlines():
            match = TASK_LINE.match(line)
            if not match:
                continue

            task_id = match.group("id")
            details = metadata.get(task_id, {})
            status = details.get("status")
            if status is None:
                status = "done" if match.group("done").lower() == "x" else "pending"

            task = graph.upsert_node(
                "Task", "id", task_id,
                title=match.group("title").strip(),
                status=str(status),
                priority=details.get("priority"),
                source_path=source_path,
            )

            if parent_spec_id:
                spec = graph.upsert_node("Spec", "id", str(parent_spec_id))
                graph.add_edge(spec, "DECOMPOSED_INTO", task)

            for dependency_id in details.get("depends_on", []) or []:
                dep = graph.upsert_node("Task", "id", str(dependency_id))
                graph.add_edge(task, "DEPENDS_ON", dep)

            for code_path in details.get("implements", []) or []:
                code_path = str(code_path)
                code = graph.upsert_node(
                    "CodeArtifact", "path", code_path,
                    kind="code", exists=(repo_root / code_path).exists(),
                )
                graph.add_edge(task, "IMPLEMENTED_BY", code)

            for test_path in details.get("validated_by", []) or []:
                test_path = str(test_path)
                test = graph.upsert_node(
                    "Test", "path", test_path,
                    kind="test", exists=(repo_root / test_path).exists(),
                )
                graph.add_edge(task, "VALIDATED_BY", test)
