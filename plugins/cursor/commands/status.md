---
allowed-tools: Bash(node *)
description: Show Cursor companion jobs — a job id for detail, or nothing for the recent list in this workspace.
---

Show the status of Cursor agent jobs.

Argument (optional job id): $ARGUMENTS

Run exactly one Bash call and return its output as-is:

```
node "${CLAUDE_PLUGIN_ROOT}/scripts/cursor-companion.mjs" status $ARGUMENTS
```

If `$ARGUMENTS` is empty this lists recent jobs for the current workspace; pass `--all` to see every workspace. With a job id it shows that job's detail. For a finished job, fetch its output with `/cursor:result <id>`.
