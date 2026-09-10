
# Spec Kit in MyHub

MyHub uses one root-scoped Spec Kit project during V0.x.

Initialize/refresh the official managed Spec Kit assets with the official CLI,
then review the diff before committing.

Examples:

```bash
specify init --here --force --integration opencode
# or
specify init --here --force --integration claude
```

Use `specify integration list` to see integrations supported by the installed
Spec Kit version.

The canonical project constitution is:

```text
.specify/memory/constitution.md
```

Do not replace project-authored constitution content without review.
