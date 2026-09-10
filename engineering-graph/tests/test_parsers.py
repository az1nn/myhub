from pathlib import Path

from sync.model import GraphModel
from sync.specs import sync_specs
from sync.tasks import sync_tasks


def test_specs_and_tasks_build_traceability(tmp_path: Path):
    feature = tmp_path / "specs" / "001-example"
    feature.mkdir(parents=True)

    (feature / "spec.md").write_text(
        """---
id: SPEC-EXAMPLE
type: spec
status: active
requires:
  - REQ-EXAMPLE
critical_requirements:
  - REQ-EXAMPLE
constrained_by:
  - ADR-001
---
# Example
""",
        encoding="utf-8",
    )

    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "example.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "tests" / "test_example.py").write_text("def test_ok(): assert True\n", encoding="utf-8")

    (feature / "tasks.md").write_text(
        """---
id: TASKSET-EXAMPLE
type: tasks
spec_id: SPEC-EXAMPLE
task_metadata:
  TASK-EXAMPLE-01:
    implements:
      - src/example.py
    validated_by:
      - tests/test_example.py
---
# Tasks

- [x] TASK-EXAMPLE-01 Implement example.
""",
        encoding="utf-8",
    )

    graph = GraphModel()
    sync_specs(tmp_path, graph)
    sync_tasks(tmp_path, graph)

    assert len(graph.find("Requirement")) == 1
    assert len(graph.find("Spec")) == 1
    assert len(graph.find("Task")) == 1
    assert len(graph.find("CodeArtifact")) == 1
    assert len(graph.find("Test")) == 1
