# Traceability Model

```text
Requirement
   ↓ REALIZED_BY
Spec
   ↓ DECOMPOSED_INTO
Task
   ├── IMPLEMENTED_BY → CodeArtifact
   └── VALIDATED_BY   → Test

Spec ── CONSTRAINED_BY → ADR
Task ── DEPENDS_ON      → Task
Spec ── DEPENDS_ON      → Spec

PullRequest
   ├── IMPLEMENTS → Task
   └── CHANGES    → CodeArtifact
```

Stable identifiers and deterministic repository evidence are preferred over
AI-inferred relationships.
