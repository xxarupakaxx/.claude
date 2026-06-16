---
allowed-tools: Bash(node *)
description: Print the full result of a finished Cursor companion job (defaults to the latest job in this workspace).
---

Print the full result text of a finished Cursor agent job.

Argument (optional job id): $ARGUMENTS

Run exactly one Bash call and return its output as-is:

```
node "${CLAUDE_PLUGIN_ROOT}/scripts/cursor-companion.mjs" result $ARGUMENTS
```

With no argument it returns the most recent job for the current workspace. If the job is still running, it says so — re-check with `/cursor:status`.
