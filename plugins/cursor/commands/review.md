---
description: Run a Cursor code review against local git state (non-Claude cross-vendor review)
argument-hint: '[--wait|--background] [--base <ref>] [--model <opus|gpt-5.5>] [focus ...]'
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Bash(node:*), Bash(git:*), AskUserQuestion
---

Run a Cursor review through the shared companion runtime.

Raw slash-command arguments:
`$ARGUMENTS`

Core constraint:
- This command is review-only.
- Do not fix issues, apply patches, or suggest that you are about to make changes.
- Your only job is to run the review and return Cursor's output verbatim to the user.

Execution mode rules:
- If the raw arguments include `--wait`, do not ask. Run in the foreground.
- If the raw arguments include `--background`, do not ask. Run in a Claude background task.
- Otherwise, estimate the review size:
  - `git diff --shortstat --cached` and `git diff --shortstat` for working-tree.
  - `git diff --shortstat <base>...HEAD` for base-branch review.
  - Recommend waiting for small reviews (1-2 files), background otherwise.
- Then use `AskUserQuestion` exactly once:
  - `Wait for results` / `Run in background`

Review target resolution:
- Default: working-tree changes (staged + unstaged)
- `--base <ref>`: review all commits since ref (`git diff <ref>...HEAD`)
- If no changes are found, say so and stop.

Building the review prompt:
1. Collect the diff: `git diff HEAD` (or `git diff <base>...HEAD`)
2. Build a review prompt that includes the diff and asks Cursor to:
   - Find correctness bugs, logic errors, security issues
   - Check for regressions and edge cases
   - Note code quality and maintainability concerns
   - Output structured findings with file:line references
3. If the user supplied focus text, append it as additional review guidance.

Foreground flow:
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/cursor-companion.mjs" task --read-only --model <model> "<review prompt with diff>"
```
- Return the command stdout verbatim, exactly as-is.
- Do not fix any issues mentioned in the review output.

Background flow:
```typescript
Bash({
  command: `node "${CLAUDE_PLUGIN_ROOT}/scripts/cursor-companion.mjs" task --background --read-only --model <model> "<review prompt>"`,
  description: "Cursor review",
  run_in_background: true
})
```
- Tell the user: "Cursor review started in the background. Check `/cursor:status` for progress."
