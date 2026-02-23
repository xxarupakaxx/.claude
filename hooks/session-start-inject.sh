#!/bin/bash
# session-start-inject.sh
# コンテキスト圧縮後にHANDOVER.mdの内容を注入する
# SessionStart (compact) で発火

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // ""')

if [ -z "$CWD" ]; then
  exit 0
fi

HANDOVER_FILE="$CWD/.local/HANDOVER.md"

if [ -f "$HANDOVER_FILE" ]; then
  echo "=== SESSION HANDOVER (auto-injected after compaction) ==="
  echo ""
  cat "$HANDOVER_FILE"
  echo ""
  echo "=== END HANDOVER ==="
fi

exit 0
