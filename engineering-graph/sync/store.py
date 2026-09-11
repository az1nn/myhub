from __future__ import annotations

from neo4j import GraphDatabase

from .model import GraphModel


ALLOWED_LABELS = {"Requirement", "Spec", "ADR", "Task", "CodeArtifact", "Test", "PullRequest"}
ALLOWED_RELATIONSHIPS = {"REALIZED_BY", "CONSTRAINED_BY", "DECOMPOSED_INTO", "DEPENDS_ON", "IMPLEMENTED_BY", "VALIDATED_BY", "IMPLEMENTS", "CHANGES"}


def _identifier(value: str, allowed: set[str]) -> str:
    if value not in allowed:
        raise ValueError(f"Unsupported graph identifier: {value}")
    return value


class Neo4jStore:
    def __init__(self, uri: str, user: str, password: str) -> None:
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self.driver.close()

    def verify_connectivity(self) -> None:
        self.driver.verify_connectivity()

    def rebuild(self, graph: GraphModel) -> None:
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n").consume()

            for node in graph.nodes.values():
                label = _identifier(node.ref.label, ALLOWED_LABELS)
                key = node.ref.key_name
                if key not in {"id", "path", "number"}:
                    raise ValueError(f"Unsupported node key: {key}")
                query = f"MERGE (n:{label} {{{key}: $key_value}}) SET n += $properties"
                session.run(query, key_value=node.ref.key_value, properties=node.properties).consume()

            for edge in graph.edges:
                rel = _identifier(edge.rel_type, ALLOWED_RELATIONSHIPS)
                source_label = _identifier(edge.source.label, ALLOWED_LABELS)
                target_label = _identifier(edge.target.label, ALLOWED_LABELS)
                source_key = edge.source.key_name
                target_key = edge.target.key_name
                query = (
                    f"MATCH (a:{source_label} {{{source_key}: $source}}), "
                    f"(b:{target_label} {{{target_key}: $target}}) "
                    f"MERGE (a)-[:{rel}]->(b)"
                )
                session.run(query, source=edge.source.key_value, target=edge.target.key_value).consume()

    def counts(self) -> dict[str, int]:
        with self.driver.session() as session:
            result = session.run("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count ORDER BY label")
            return {record["label"]: record["count"] for record in result}
