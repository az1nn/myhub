// Parameters: $task_id
MATCH (task:Task {id: $task_id})
OPTIONAL MATCH (spec:Spec)-[:DECOMPOSED_INTO]->(task)
OPTIONAL MATCH (req:Requirement)-[:REALIZED_BY]->(spec)
OPTIONAL MATCH (spec)-[:CONSTRAINED_BY]->(adr:ADR)
OPTIONAL MATCH (task)-[:DEPENDS_ON]->(dependency:Task)
OPTIONAL MATCH (task)-[:IMPLEMENTED_BY]->(code:CodeArtifact)
OPTIONAL MATCH (task)-[:VALIDATED_BY]->(test:Test)
RETURN task,
       collect(DISTINCT spec) AS specs,
       collect(DISTINCT req) AS requirements,
       collect(DISTINCT adr) AS adrs,
       collect(DISTINCT dependency) AS dependencies,
       collect(DISTINCT code) AS code_artifacts,
       collect(DISTINCT test) AS tests;
