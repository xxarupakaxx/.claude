---
description: Delegate investigation, an explicit fix request, or follow-up rescue work to the Cursor rescue subagent
argument-hint: "[--background|--wait] [--resume-last|--fresh] [--model <opus|gpt-5.5>] [--read-only] [what Cursor should investigate, solve, or continue]"
allowed-tools: Bash(node:*), AskUserQuestion, Agent
---

Invoke the `cursor:cursor-rescue` subagent via the `Agent` tool (`subagent_type: "cursor:cursor-rescue"`), forwarding the raw user request as the prompt.
`cursor:cursor-rescue` is a subagent, not a skill — do not call `Skill(cursor:cursor-rescue)` or `Skill(cursor:rescue)` (that re-enters this command and hangs the session).
The final user-visible response must be Cursor's output verbatim.

Raw user request:
$ARGUMENTS

Execution mode:

- If the request includes `--background`, run the `cursor:cursor-rescue` subagent in the background.
- If the request includes `--wait`, run the subagent in the foreground.
- If neither flag is present, default to foreground.
- `--background` and `--wait` are execution flags for Claude Code. Do not forward them to `task`.
- `--model` is a runtime-selection flag. Preserve it for the forwarded `task` call.
- If the request includes `--resume-last`, do not ask whether to continue.
- If the request includes `--fresh`, do not ask whether to continue.
- Otherwise, before starting Cursor, check for a resumable session by running:

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/cursor-companion.mjs" status --json 2>/dev/null | head -1
```

- If there is a recent completed task, use `AskUserQuestion` exactly once:
  - `Continue current Cursor thread`
  - `Start a new Cursor thread`
- If the user chooses continue, add `--resume-last`.
- If the user chooses new, add `--fresh`.

Operating rules:

- The subagent is a thin forwarder only. It should use one `Bash` call to invoke `node "${CLAUDE_PLUGIN_ROOT}/scripts/cursor-companion.mjs" task ...` and return that command's stdout as-is.
- Return the Cursor companion stdout verbatim to the user.
- Do not paraphrase, summarize, rewrite, or add commentary before or after it.
- Do not ask the subagent to inspect files, monitor progress, fetch results, or do follow-up work.
- If the user did not supply a request, ask what Cursor should investigate or fix.
