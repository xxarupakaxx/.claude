#!/bin/bash
# post-skill-usage-track.sh
# Skillツール使用時にスキル名・タイムスタンプ・プロジェクトを記録する

INPUT=$(cat)
SKILL_NAME=$(echo "$INPUT" | jq -r '.tool_input.skill // empty')

# スキル名が取得できなければ何もしない
if [ -z "$SKILL_NAME" ]; then
  exit 0
fi

USAGE_FILE="$HOME/.claude/skill-usage.jsonl"
O
jq -n \
  --arg skill "$SKILL_NAME" \
  --arg ts "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  --arg project "$PWD" \
  '{skill: $skill, timestamp: $ts, project: $project}' >> "$USAGE_FILE"

exit 0
