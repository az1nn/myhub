from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess

from .model import GraphModel

TASK_ID = re.compile(r"\bTASK-[A-Z0-9-]+\b")


def _changed_files(repo_root: Path, base_sha: str | None, head_sha: str | None) -> list[str]:
    if not base_sha or not head_sha:
        return []
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_sha}...{head_sha}"],
            cwd=repo_root, check=True, capture_output=True, text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def sync_pull_request(repo_root: Path, graph: GraphModel) -> None:
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if not event_path:
        return
    path = Path(event_path)
    if not path.exists():
        return

    payload = json.loads(path.read_text(encoding="utf-8"))
    pr = payload.get("pull_request")
    if not isinstance(pr, dict):
        return

    number = pr.get("number") or payload.get("number")
    if number is None:
        return

    title = str(pr.get("title") or "")
    body = str(pr.get("body") or "")
    head_ref = str((pr.get("head") or {}).get("ref") or "")
    base_sha = (pr.get("base") or {}).get("sha")
    head_sha = (pr.get("head") or {}).get("sha")

    pr_node = graph.upsert_node(
        "PullRequest", "number", int(number),
        title=title, state=str(pr.get("state") or "open"),
        url=pr.get("html_url"), head_sha=head_sha, base_sha=base_sha, head_ref=head_ref,
    )

    task_ids = set(TASK_ID.findall("\n".join([title, body, head_ref])))
    for task_id in sorted(task_ids):
        task = graph.upsert_node("Task", "id", task_id)
        graph.add_edge(pr_node, "IMPLEMENTS", task)

    for changed_path in _changed_files(repo_root, base_sha, head_sha):
        artifact = graph.upsert_node(
            "CodeArtifact", "path", changed_path,
            kind="changed", exists=(repo_root / changed_path).exists(),
        )
        graph.add_edge(pr_node, "CHANGES", artifact)
