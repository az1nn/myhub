from sync.model import GraphModel
from validate.invariants import validate_graph


def codes(graph: GraphModel) -> set[str]:
    return {issue.code for issue in validate_graph(graph)}


def test_detects_active_spec_without_task():
    graph = GraphModel()
    graph.upsert_node("Spec", "id", "SPEC-1", status="active")
    assert "ACTIVE_SPEC_WITHOUT_TASK" in codes(graph)


def test_detects_done_task_without_implementation():
    graph = GraphModel()
    graph.upsert_node("Task", "id", "TASK-1", status="done", source_path="specs/x/tasks.md")
    assert "DONE_TASK_WITHOUT_IMPLEMENTATION" in codes(graph)


def test_detects_task_dependency_cycle():
    graph = GraphModel()
    a = graph.upsert_node("Task", "id", "TASK-A", status="pending", source_path="a")
    b = graph.upsert_node("Task", "id", "TASK-B", status="pending", source_path="b")
    graph.add_edge(a, "DEPENDS_ON", b)
    graph.add_edge(b, "DEPENDS_ON", a)
    assert "TASK_DEPENDENCY_CYCLE" in codes(graph)


def test_pending_spec_does_not_require_validation_evidence_yet():
    graph = GraphModel()
    req = graph.upsert_node("Requirement", "id", "REQ-PLANNED", critical=True)
    spec = graph.upsert_node("Spec", "id", "SPEC-PLANNED", status="active")
    task = graph.upsert_node("Task", "id", "TASK-PLANNED", status="pending", source_path="specs/planned/tasks.md")
    graph.add_edge(req, "REALIZED_BY", spec)
    graph.add_edge(spec, "DECOMPOSED_INTO", task)

    assert "CRITICAL_REQUIREMENT_WITHOUT_VALIDATION" not in codes(graph)


def test_completed_spec_requires_real_validation_evidence():
    graph = GraphModel()
    req = graph.upsert_node("Requirement", "id", "REQ-DONE", critical=True)
    spec = graph.upsert_node("Spec", "id", "SPEC-DONE", status="active")
    task = graph.upsert_node("Task", "id", "TASK-DONE", status="done", source_path="specs/done/tasks.md")
    code = graph.upsert_node("CodeArtifact", "path", "src/x.py", exists=True)
    graph.add_edge(req, "REALIZED_BY", spec)
    graph.add_edge(spec, "DECOMPOSED_INTO", task)
    graph.add_edge(task, "IMPLEMENTED_BY", code)

    assert "CRITICAL_REQUIREMENT_WITHOUT_VALIDATION" in codes(graph)


def test_planning_only_pr_may_exist_without_implements_edge():
    graph = GraphModel()
    pr = graph.upsert_node("PullRequest", "number", 10)
    changed = graph.upsert_node("CodeArtifact", "path", "specs/008-push-notifications/spec.md", exists=True)
    graph.add_edge(pr, "CHANGES", changed)

    assert "PR_WITHOUT_TASK_TRACEABILITY" not in codes(graph)


def test_code_pr_still_requires_task_traceability():
    graph = GraphModel()
    pr = graph.upsert_node("PullRequest", "number", 11)
    changed = graph.upsert_node("CodeArtifact", "path", "services/api/src/myhub/app.py", exists=True)
    graph.add_edge(pr, "CHANGES", changed)

    assert "PR_WITHOUT_TASK_TRACEABILITY" in codes(graph)


def test_code_pr_with_implements_edge_passes_pr_traceability():
    graph = GraphModel()
    pr = graph.upsert_node("PullRequest", "number", 12)
    task = graph.upsert_node("Task", "id", "TASK-12", status="pending", source_path="specs/x/tasks.md")
    changed = graph.upsert_node("CodeArtifact", "path", "services/api/src/myhub/app.py", exists=True)
    graph.add_edge(pr, "CHANGES", changed)
    graph.add_edge(pr, "IMPLEMENTS", task)

    assert "PR_WITHOUT_TASK_TRACEABILITY" not in codes(graph)


def test_valid_traceability_passes():
    graph = GraphModel()
    req = graph.upsert_node("Requirement", "id", "REQ-1", critical=True)
    spec = graph.upsert_node("Spec", "id", "SPEC-1", status="active")
    task = graph.upsert_node("Task", "id", "TASK-1", status="done", source_path="tasks.md")
    code = graph.upsert_node("CodeArtifact", "path", "src/x.py", exists=True)
    test = graph.upsert_node("Test", "path", "tests/test_x.py", exists=True)
    graph.add_edge(req, "REALIZED_BY", spec)
    graph.add_edge(spec, "DECOMPOSED_INTO", task)
    graph.add_edge(task, "IMPLEMENTED_BY", code)
    graph.add_edge(task, "VALIDATED_BY", test)
    assert validate_graph(graph) == []
