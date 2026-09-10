MATCH (t:Task)
WHERE t.status = 'pending'
  AND NOT EXISTS {
    MATCH (t)-[:DEPENDS_ON]->(dependency:Task)
    WHERE dependency.status <> 'done'
  }
RETURN t.id AS task_id, t.priority AS priority
ORDER BY priority, task_id;
