from __future__ import annotations

import argparse
from pathlib import Path
import sys

from sync.sync import build_graph
from validate.invariants import validate_graph


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate MyHub Engineering Graph invariants")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    graph = build_graph(args.repo_root.resolve())
    issues = validate_graph(graph)
    if not issues:
        print(f"Engineering Graph valid: nodes={len(graph.nodes)} edges={len(graph.edges)}")
        return
    for issue in issues:
        print(f"{issue.severity} {issue.code} [{issue.subject}] {issue.message}")
    if any(issue.severity == "ERROR" for issue in issues):
        sys.exit(1)


if __name__ == "__main__":
    main()
