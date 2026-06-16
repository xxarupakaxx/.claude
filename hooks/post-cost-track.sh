#!/bin/bash
# PostToolUse hook: ツール呼び出しをコスト追跡ログに記録
# settings.json の PostToolUse で呼び出される

TRACK_DIR="${HOME}/.claude/.local/cost-track"
mkdir -p "$TRACK_DIR"

DATE=$(date +%Y%m%d)
TRACK_FILE="${TRACK_DIR}/${DATE}.log"

# stdin から JSON を読み取り、ツール名を抽出
INPUT=$(cat)
if command -v jq &>/dev/null; then
  TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // "unknown"' 2>/dev/null)
else
  TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"tool_name"[[:space:]]*:[[:space:]]*"//' | sed 's/"//')
fi

if [ -z "$TOOL_NAME" ]; then
  TOOL_NAME="unknown"
fi

# 時刻とツール名をログに追記
echo "$(date +%H:%M:%S) ${TOOL_NAME}" >> "$TRACK_FILE"
