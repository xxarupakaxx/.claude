#!/bin/bash
# taskCompleted-compound.sh
# TaskCompleted (Claude Code v2.1.33+): サブエージェント完了時に compounding-knowledge 提案
#
# 動作:
# - サブエージェントが完了したタイミングで、価値ある知見が生まれた可能性を示唆
# - ユーザー側で /skill compounding-knowledge を起動する判断材料を提供
# - JSON 1行を ~/.claude/.local/hooks/log/task_completed.jsonl に追記

INPUT=$(cat)
TASK_NAME=$(echo "$INPUT" | jq -r '.task_name // .agent_name // ""')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // ""')

LOG_DIR="$HOME/.claude/.local/hooks/log"
mkdir -p "$LOG_DIR" 2>/dev/null

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ログ追記
printf '{"timestamp":"%s","session_id":"%s","task_name":%s}\n' \
  "$TIMESTAMP" "$SESSION_ID" \
  "$(jq -nc --arg t "$TASK_NAME" '$t')" \
  >> "$LOG_DIR/task_completed.jsonl"

# 知見保存の対象になりそうなタスク名パターン (調査・設計・問題解決系)
if echo "$TASK_NAME" | grep -qiE '(investigate|research|design|debug|adversarial|review|stocktake|analyse)'; then
  cat >&2 <<EOF
[Compound Suggestion] サブエージェント '$TASK_NAME' が完了しました。
価値ある知見が得られた場合、/skill compounding-knowledge で構造化保存を検討してください。
EOF
fi

exit 0
