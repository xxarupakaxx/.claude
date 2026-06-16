---
allowed-tools: Bash(node:*), Bash(cursor-agent:*), Bash(which:*)
description: Check whether cursor-agent CLI is installed and ready
---

Check the Cursor agent CLI setup status.

Run exactly one Bash call and return its output as-is:

```
node "${CLAUDE_PLUGIN_ROOT}/scripts/cursor-companion.mjs" doctor
```

If cursor-agent is not found, tell the user to install it:
- `npm install -g @anthropic-ai/cursor-agent` or check https://docs.cursor.com/agent
- Then `cursor-agent login` to authenticate.
