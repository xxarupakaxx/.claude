#!/bin/bash
# pre-git-push-remind.sh
# PreToolUse: git push前に変更レビューを促す警告（standard: 警告のみ）

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')

if [ "$TOOL" != "Bash" ]; then
  exit 0
fi

CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

if [ -z "$CMD" ]; then
  exit 0
fi

# git pushの検出
if ! echo "$CMD" | grep -qE 'git\s+push'; then
  exit 0
fi

# --dry-run の場合はスキップ
if echo "$CMD" | grep -qE '\-\-dry-run'; then
  exit 0
fi

CWD=$(echo "$INPUT" | jq -r '.cwd // ""')

# 未コミットの変更があるかチェック
if [ -n "$CWD" ] && [ -d "$CWD/.git" ]; then
  UNCOMMITTED=$(cd "$CWD" && git status --porcelain 2>/dev/null | head -5)
  if [ -n "$UNCOMMITTED" ]; then
    echo '[Hook] WARNING: 未コミットの変更があります:' >&2
    echo "$UNCOMMITTED" >&2
    echo '[Hook] コミット忘れがないか確認してください' >&2
  fi
fi

# push先のブランチ情報を表示
BRANCH=$(cd "$CWD" 2>/dev/null && git branch --show-current 2>/dev/null)
if [ -n "$BRANCH" ]; then
  AHEAD=$(cd "$CWD" 2>/dev/null && git rev-list --count @{u}..HEAD 2>/dev/null || echo "?")
  echo "[Hook] REMINDER: ${BRANCH} ブランチに ${AHEAD} コミットをpushします" >&2
fi

exit 0
