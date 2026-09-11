from __future__ import annotations

from dataclasses import dataclass

from sync.model import GraphModel, GraphNode, NodeRef


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    subject: str
    severity: str
    message: str


_PLANNING_ARTIFACT_PREFIXES = (
    "docs/",
    "specs/",
    ".specify/",
)


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
        # Critical requirements become a merge gate for validation evidence only
        # when their realized spec is implementation-complete. Planned/active
        # specs with pending tasks are expected to have requirements that are not
        # validated yet; blocking them would make the control plane reject its
        # own incremental delivery model.
        completed_specs = _completed_realized_specs(graph, req)
        if not completed_specs:
            continue
        if not _has_real_validation_evidence(graph, completed_specs):
            issues.append(ValidationIssue("CRITICAL_REQUIREMENT_WITHOUT_VALIDATION", str(req.ref.key_value), "ERROR", "Critical Requirement belongs to a completed Spec but has no traceable validation evidence."))

    declared_tasks = {task.ref for task in graph.find("Task") if task.properties.get("source_path") is not None}
    for edge in graph.edges:
        if edge.rel_type == "DEPENDS_ON" and edge.source.label == "Task" and edge.target not in declared_tasks:
            issues.append(ValidationIssue("UNKNOWN_TASK_DEPENDENCY", str(edge.source.key_value), "ERROR", f"Dependency is not declared: {edge.target.key_value}"))

    issues.extend(_validate_task_cycles(graph))

    for pr in graph.find("PullRequest"):
        if graph.outgoing(pr.ref, "IMPLEMENTS"):
            continue
        if _pr_requires_task_traceability(graph, pr):
            issues.append(ValidationIssue("PR_WITHOUT_TASK_TRACEABILITY", str(pr.ref.key_value), "ERROR", "Code/runtime/control-plane Pull Request has no IMPLEMENTS Task relationship."))

    return issues


def _completed_realized_specs(graph: GraphModel, requirement: GraphNode) -> list[NodeRef]:
    completed: list[NodeRef] = []
    for realized in graph.outgoing(requirement.ref, "REALIZED_BY"):
        task_edges = graph.outgoing(realized.target, "DECOMPOSED_INTO")
        if not task_edges:
            continue
        task_nodes = [graph.nodes.get(edge.target) for edge in task_edges]
        if all(node is not None and node.properties.get("status") == "done" for node in task_nodes):
            completed.append(realized.target)
    return completed


def _has_real_validation_evidence(graph: GraphModel, specs: list[NodeRef]) -> bool:
    for spec_ref in specs:
        for task_edge in graph.outgoing(spec_ref, "DECOMPOSED_INTO"):
            task = graph.nodes.get(task_edge.target)
            if task is None or task.properties.get("status") != "done":
                continue
            for validation_edge in graph.outgoing(task.ref, "VALIDATED_BY"):
                test = graph.nodes.get(validation_edge.target)
                if test is not None and test.properties.get("exists") is not False:
                    return True
    return False


def _pr_requires_task_traceability(graph: GraphModel, pr: GraphNode) -> bool:
    changes = graph.outgoing(pr.ref, "CHANGES")
    if not changes:
        # If change classification is unavailable, fail closed rather than
        # silently exempting an implementation PR from traceability.
        return True

    for edge in changes:
        path = str(edge.target.key_value)
        if not path.startswith(_PLANNING_ARTIFACT_PREFIXES):
            return True
    return False


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
