#!/bin/bash
# team-budget-guard.sh
# SubagentStop: team-run の差し戻し回数を Team Journal の Attribution 節から数え、
# Budget(差し戻し閾値) 超過を検知して loop を止め、human に escalate する。
#
# 設計:
# - 差し戻しの「真実の源」は Team Journal の「## 失敗・差し戻し Attribution」節の行
#   (leader が S7 で差し戻しのたびに1行記録する)。hook はそれを数えるだけ。
#   → 公式非公開の入力JSONフィールドに依存しない
# - team-journal.md が無ければ team-run 文脈でない → exit 0
# - 閾値超過なら exit 2 で leader に停止を促す + Bark で human に通知
# - fail-safe: 異常時は exit 0(メイン処理を止めない)

INPUT=$(cat)
[ "$(echo "$INPUT" | jq -r '.stop_hook_active // false')" = "true" ] && exit 0

# Agent Teams 文脈でなければ何もしない
[ "${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-}" = "1" ] || exit 0

# 最新の team-journal.md を探す
JOURNAL=$(find "$HOME/.claude/.local/memory" -name "team-journal.md" -type f -print0 2>/dev/null | xargs -0 ls -t 2>/dev/null | head -1)
[ -z "$JOURNAL" ] && exit 0

# Attribution 節のデータ行のみ数える(ヘッダ=agent含む行・区切り=| -始まり を明示除外)
RETRIES=$(awk '
  /## 失敗・差し戻し Attribution/ {f=1; next}
  /^## / {f=0}
  f && /^\|/ && !/agent/ && !/^\| *-/ {c++}
  END {print c+0}
' "$JOURNAL" 2>/dev/null)
[ -z "$RETRIES" ] && RETRIES=0

THRESHOLD=3
if [ "$RETRIES" -gt "$THRESHOLD" ]; then
  cat >&2 <<EOF
[Budget Guard] Team Journal の差し戻しが ${RETRIES}回（閾値 ${THRESHOLD}）を超えています。
loop を止めて、残タスクと進捗を human に escalate してください（autonomous-loops の Stop 条件）。
EOF
  if [ -n "$BARK_DEVICE_KEY" ]; then
    bash "$HOME/.claude/hooks/bark-notify.sh" <<< "{\"title\":\"team-run Budget超過\",\"body\":\"差し戻し${RETRIES}回\"}" 2>/dev/null || true
  fi
  exit 2
fi

exit 0
