#!/bin/bash
# Stop: consume exact-session numeric metrics and save a bounded suggestion.

CORE="${HOOK_OBSERVATIONS_SCRIPT:-$HOME/.claude/scripts/hook_observations.py}"
if [ ! -f "$CORE" ]; then
  printf '%s\n' '{"hook":"stop-suggestion","status":"unsupported","reason":"helper_missing"}' >&2
  exit 0
fi

exec python3 "$CORE" stop --runtime claude
