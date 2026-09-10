from sync.model import GraphModel


def test_graph_model_deduplicates_nodes_and_edges():
    graph = GraphModel()
    spec = graph.upsert_node("Spec", "id", "SPEC-1", status="active")
    same_spec = graph.upsert_node("Spec", "id", "SPEC-1", title="Example")
    task = graph.upsert_node("Task", "id", "TASK-1", status="pending")

    graph.add_edge(spec, "DECOMPOSED_INTO", task)
    graph.add_edge(same_spec, "DECOMPOSED_INTO", task)

    assert spec == same_spec
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.nodes[spec].properties["title"] == "Example"
