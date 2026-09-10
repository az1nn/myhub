"""MyHub Engineering Graph synchronization entry point.

V1 deliberately synchronizes only explicit repository metadata.
No AI-inferred relationships and no full AST analysis.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def main() -> None:
    print("MyHub Graph Sync scaffold")
    print(f"Repository: {REPO_ROOT}")
    print("Next implementation: parse Spec Kit artifacts, ADRs, tasks, code/test paths and Git metadata deterministically.")

if __name__ == "__main__":
    main()
