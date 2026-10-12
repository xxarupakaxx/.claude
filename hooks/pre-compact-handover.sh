#!/bin/bash
set -u

CORE="${SESSION_HANDOVER_CORE:-}"
if [ -z "$CORE" ]; then
  CODEX_ROOT="${CODEX_HOME:-$HOME/.codex}"
  CORE="$CODEX_ROOT/scripts/session_handover.py"
fi
if [ ! -f "$CORE" ]; then
  printf '%s\n' 'session-handover: core_not_found' >&2
  exit 0
fi
exec python3 "$CORE" hook --runtime claude --event PreCompact
