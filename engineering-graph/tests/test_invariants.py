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
