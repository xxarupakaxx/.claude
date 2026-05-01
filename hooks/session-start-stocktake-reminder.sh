#!/bin/bash
# session-start-stocktake-reminder.sh
# 月初(1-5日)のSessionStart時に skill-stocktake 実行を提案するリマインダー。
# 当月すでにリマインド済みならスキップする。リマインド自体は提案のみで自動実行はしない。

set -uo pipefail

DAY_OF_MONTH=$(date +%-d)

if [ "$DAY_OF_MONTH" -gt 5 ]; then
  exit 0
fi

CURRENT_MONTH=$(date +%Y-%m)
STATE_FILE="$HOME/.claude/.local/skill-stocktake-reminded.txt"

if [ -f "$STATE_FILE" ]; then
  LAST_REMINDED=$(head -1 "$STATE_FILE" 2>/dev/null | tr -d '[:space:]')
  if [ "$LAST_REMINDED" = "$CURRENT_MONTH" ]; then
    exit 0
  fi
fi

mkdir -p "$(dirname "$STATE_FILE")"
echo "$CURRENT_MONTH" > "$STATE_FILE"

cat <<'EOF'
📋 月初リマインド: 前回の棚卸しから時間が経っています。
`/skill-stocktake` で全スキルの棚卸し（KEEP/IMPROVE/RETIRE/MERGE 判定）を実行できます。
※ Skillツール経由でない参照型スキル（learnings-researcher等）は使用回数に記録されないため、「未使用＝不要」ではない点に注意。
EOF

exit 0
