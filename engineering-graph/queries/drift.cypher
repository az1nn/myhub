CALL {
  MATCH (s:Spec)
  WHERE s.status = 'active'
    AND NOT EXISTS { MATCH (s)-[:DECOMPOSED_INTO]->(:Task) }
  RETURN 'ACTIVE_SPEC_WITHOUT_TASK' AS issue, s.id AS subject
  UNION
  MATCH (t:Task)
  WHERE t.status = 'done'
    AND NOT EXISTS { MATCH (t)-[:IMPLEMENTED_BY]->(:CodeArtifact) }
  RETURN 'DONE_TASK_WITHOUT_IMPLEMENTATION' AS issue, t.id AS subject
  UNION
  MATCH (r:Requirement)
  WHERE coalesce(r.critical, false) = true
    AND NOT EXISTS {
      MATCH (r)-[:REALIZED_BY]->(:Spec)-[:DECOMPOSED_INTO]->(:Task)-[:VALIDATED_BY]->(:Test)
    }
  RETURN 'CRITICAL_REQUIREMENT_WITHOUT_VALIDATION' AS issue, r.id AS subject
}
RETURN issue, subject
ORDER BY issue, subject;
