---
description: Run a Cursor review that challenges the implementation approach and design choices (non-Claude cross-vendor adversarial review)
argument-hint: '[--wait|--background] [--base <ref>] [--model <opus|gpt-5.5>] [focus ...]'
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Bash(node:*), Bash(git:*), AskUserQuestion
---

Run an adversarial Cursor review through the shared companion runtime.
Position it as a challenge review that questions the chosen implementation, design choices, tradeoffs, and assumptions — not just a stricter pass over implementation defects.

Raw slash-command arguments:
`$ARGUMENTS`

Core constraint:
- This command is review-only.
- Do not fix issues, apply patches, or suggest that you are about to make changes.
- Your only job is to run the review and return Cursor's output verbatim to the user.
- Keep the framing focused on whether the current approach is the right one, what assumptions it depends on, and where the design could fail under real-world conditions.

Execution mode rules:
- Same as `/cursor:review` — estimate size, ask foreground vs background.

Building the adversarial review prompt:
1. Collect the diff: `git diff HEAD` (or `git diff <base>...HEAD`)
2. Build a review prompt that includes the diff and instructs Cursor to:
   - **Challenge the approach**: Is this the right design? What alternatives were discarded, and should they have been?
   - **Question assumptions**: What does this code assume about callers, data shape, ordering, concurrency?
   - **Find failure modes**: Auth bypass, data destruction, rollback safety, race conditions, schema drift
   - **Check observability**: Can you debug this in production? Are failures silent?
   - Output structured findings: file, line, confidence (high/medium/low), category, recommendation
   - Final verdict: `needs-attention` or `approve`
3. If the user supplied focus text, append it as additional adversarial guidance.

Foreground flow:
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/cursor-companion.mjs" task --read-only --model <model> "<adversarial review prompt with diff>"
```
- Return the command stdout verbatim.

Background flow:
- Same as `/cursor:review` but with adversarial framing.
- Tell the user: "Cursor adversarial review started in the background. Check `/cursor:status` for progress."
