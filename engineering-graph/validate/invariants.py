from __future__ import annotations

from dataclasses import dataclass

from sync.model import GraphModel, NodeRef


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    subject: str
    severity: str
    message: str


def validate_graph(graph: GraphModel) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    for spec in graph.find("Spec"):
        if spec.properties.get("status") == "active" and not graph.outgoing(spec.ref, "DECOMPOSED_INTO"):
            issues.append(ValidationIssue("ACTIVE_SPEC_WITHOUT_TASK", str(spec.ref.key_value), "ERROR", "Active Spec has no DECOMPOSED_INTO Task relationship."))

    for task in graph.find("Task"):
        if task.properties.get("status") != "done":
            continue
        implementation_edges = graph.outgoing(task.ref, "IMPLEMENTED_BY")
        if not implementation_edges:
            issues.append(ValidationIssue("DONE_TASK_WITHOUT_IMPLEMENTATION", str(task.ref.key_value), "ERROR", "Completed Task has no IMPLEMENTED_BY relationship."))
        for edge in implementation_edges:
            node = graph.nodes.get(edge.target)
            if node is not None and node.properties.get("exists") is False:
                issues.append(ValidationIssue("MISSING_IMPLEMENTATION_ARTIFACT", str(task.ref.key_value), "ERROR", f"Declared implementation does not exist: {edge.target.key_value}"))
        for edge in graph.outgoing(task.ref, "VALIDATED_BY"):
            node = graph.nodes.get(edge.target)
            if node is not None and node.properties.get("exists") is False:
                issues.append(ValidationIssue("MISSING_TEST_ARTIFACT", str(task.ref.key_value), "ERROR", f"Declared test does not exist: {edge.target.key_value}"))

    for req in graph.find("Requirement"):
        if not req.properties.get("critical", False):
            continue
        has_validation = False
        for realized in graph.outgoing(req.ref, "REALIZED_BY"):
            for task_edge in graph.outgoing(realized.target, "DECOMPOSED_INTO"):
                if graph.outgoing(task_edge.target, "VALIDATED_BY"):
                    has_validation = True
                    break
            if has_validation:
                break
        if not has_validation:
            issues.append(ValidationIssue("CRITICAL_REQUIREMENT_WITHOUT_VALIDATION", str(req.ref.key_value), "ERROR", "Critical Requirement has no traceable validation evidence."))

    declared_tasks = {task.ref for task in graph.find("Task") if task.properties.get("source_path") is not None}
    for edge in graph.edges:
        if edge.rel_type == "DEPENDS_ON" and edge.source.label == "Task" and edge.target not in declared_tasks:
            issues.append(ValidationIssue("UNKNOWN_TASK_DEPENDENCY", str(edge.source.key_value), "ERROR", f"Dependency is not declared: {edge.target.key_value}"))

    issues.extend(_validate_task_cycles(graph))

    for pr in graph.find("PullRequest"):
        if not graph.outgoing(pr.ref, "IMPLEMENTS"):
            issues.append(ValidationIssue("PR_WITHOUT_TASK_TRACEABILITY", str(pr.ref.key_value), "ERROR", "Pull Request has no IMPLEMENTS Task relationship."))

    return issues


def _validate_task_cycles(graph: GraphModel) -> list[ValidationIssue]:
    adjacency: dict[NodeRef, list[NodeRef]] = {}
    for edge in graph.edges:
        if edge.rel_type == "DEPENDS_ON" and edge.source.label == "Task" and edge.target.label == "Task":
            adjacency.setdefault(edge.source, []).append(edge.target)

    visiting: set[NodeRef] = set()
    visited: set[NodeRef] = set()
    issues: list[ValidationIssue] = []

    def visit(node: NodeRef, stack: list[NodeRef]) -> None:
        if node in visited:
            return
        if node in visiting:
            cycle = stack[stack.index(node):] + [node]
            issues.append(ValidationIssue("TASK_DEPENDENCY_CYCLE", str(node.key_value), "ERROR", " -> ".join(str(item.key_value) for item in cycle)))
            return
        visiting.add(node)
        stack.append(node)
        for dep in adjacency.get(node, []):
            visit(dep, stack)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in list(adjacency):
        visit(node, [])
    return issues
