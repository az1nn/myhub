from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NodeRef:
    label: str
    key_name: str
    key_value: str | int


@dataclass
class Node:
    ref: NodeRef
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Edge:
    source: NodeRef
    rel_type: str
    target: NodeRef


@dataclass
class GraphModel:
    nodes: dict[NodeRef, Node] = field(default_factory=dict)
    edges: set[Edge] = field(default_factory=set)

    def upsert_node(self, label: str, key_name: str, key_value: str | int, **properties: Any) -> NodeRef:
        ref = NodeRef(label=label, key_name=key_name, key_value=key_value)
        node = self.nodes.get(ref)
        if node is None:
            node = Node(ref=ref, properties={})
            self.nodes[ref] = node
        node.properties.update({k: v for k, v in properties.items() if v is not None})
        node.properties[key_name] = key_value
        return ref

    def add_edge(self, source: NodeRef, rel_type: str, target: NodeRef) -> None:
        self.edges.add(Edge(source=source, rel_type=rel_type, target=target))

    def find(self, label: str) -> list[Node]:
        return [node for node in self.nodes.values() if node.ref.label == label]

    def outgoing(self, source: NodeRef, rel_type: str | None = None) -> list[Edge]:
        return [edge for edge in self.edges if edge.source == source and (rel_type is None or edge.rel_type == rel_type)]

    def incoming(self, target: NodeRef, rel_type: str | None = None) -> list[Edge]:
        return [edge for edge in self.edges if edge.target == target and (rel_type is None or edge.rel_type == rel_type)]
