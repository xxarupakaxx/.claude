#!/bin/bash
# PostToolUseFailure records known failures. PostToolUse records success/edit resets.

CORE="${HOOK_OBSERVATIONS_SCRIPT:-$HOME/.claude/scripts/hook_observations.py}"
if [ ! -f "$CORE" ]; then
  printf '%s\n' '{"hook":"failure-observation","status":"unsupported","reason":"helper_missing"}' >&2
  exit 0
fi

exec python3 "$CORE" observe --runtime claude
