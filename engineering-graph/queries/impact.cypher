// Parameters: $adr_id
MATCH (adr:ADR {id: $adr_id})
OPTIONAL MATCH p1=(spec:Spec)-[:CONSTRAINED_BY]->(adr)
OPTIONAL MATCH p2=(spec)-[:DECOMPOSED_INTO]->(task:Task)
OPTIONAL MATCH p3=(task)-[:IMPLEMENTED_BY|VALIDATED_BY]->(artifact)
RETURN adr, spec, task, artifact;
