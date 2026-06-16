---
allowed-tools: Bash(node *)
description: Cancel a running/queued Cursor companion job (defaults to the active job in this workspace).
---

Cancel a running or queued Cursor agent job.

Argument (optional job id): $ARGUMENTS

Run exactly one Bash call and return its output as-is:

```
node "${CLAUDE_PLUGIN_ROOT}/scripts/cursor-companion.mjs" cancel $ARGUMENTS
```

With no argument it cancels the currently active job for this workspace.
