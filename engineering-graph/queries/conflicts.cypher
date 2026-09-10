MATCH (a:Task)-[:IMPLEMENTED_BY]->(artifact:CodeArtifact)<-[:IMPLEMENTED_BY]-(b:Task)
WHERE a.id < b.id
  AND a.status = 'pending'
  AND b.status = 'pending'
RETURN a.id AS task_a,
       b.id AS task_b,
       collect(artifact.path) AS overlapping_artifacts;
