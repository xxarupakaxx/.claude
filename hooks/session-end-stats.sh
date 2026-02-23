#!/bin/bash
# session-end-stats.sh
# セッション終了時に統計情報を記録する

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // ""')
CWD=$(echo "$INPUT" | jq -r '.cwd // ""')
REASON=$(echo "$INPUT" | jq -r '.reason // "unknown"')

STATS_DIR="$HOME/.claude/.local"
mkdir -p "$STATS_DIR"
STATS_FILE="$STATS_DIR/session-stats.jsonl"

# トランスクリプトから統計を抽出
TOTAL_MESSAGES=0
USER_MESSAGES=0
ASSISTANT_MESSAGES=0
TOOL_USES=0

if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
  TOTAL_MESSAGES=$(wc -l < "$TRANSCRIPT" | tr -d ' ')
  USER_MESSAGES=$(grep -c '"role":"user"\|"type":"user"' "$TRANSCRIPT" 2>/dev/null || echo 0)
  ASSISTANT_MESSAGES=$(grep -c '"role":"assistant"\|"type":"assistant"' "$TRANSCRIPT" 2>/dev/null || echo 0)
  TOOL_USES=$(grep -c '"type":"tool_use"\|"tool_name"' "$TRANSCRIPT" 2>/dev/null || echo 0)
fi

# 統計をJSONLで記録
jq -n \
  --arg sid "$SESSION_ID" \
  --arg ts "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  --arg cwd "$CWD" \
  --arg reason "$REASON" \
  --argjson total "$TOTAL_MESSAGES" \
  --argjson user "$USER_MESSAGES" \
  --argjson assistant "$ASSISTANT_MESSAGES" \
  --argjson tools "$TOOL_USES" \
  '{
    session_id: $sid,
    ended_at: $ts,
    cwd: $cwd,
    reason: $reason,
    messages: { total: $total, user: $user, assistant: $assistant },
    tool_uses: $tools
  }' >> "$STATS_FILE"

exit 0
