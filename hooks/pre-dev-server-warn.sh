#!/bin/bash
# pre-dev-server-warn.sh
# PreToolUse: tmux外でのdevサーバー起動を警告（standard: 警告のみ）
# npm run dev, pnpm dev, yarn dev 等がtmux外で実行されるとターミナルを占有する

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')

if [ "$TOOL" != "Bash" ]; then
  exit 0
fi

CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

if [ -z "$CMD" ]; then
  exit 0
fi

# devサーバー系コマンドの検出
DEV_PATTERN='(npm\s+run\s+dev|pnpm(\s+run)?\s+dev|yarn\s+dev|bun\s+run\s+dev|next\s+dev|vite(\s+dev)?|nuxt\s+dev|remix\s+dev)'

if ! echo "$CMD" | grep -qE "$DEV_PATTERN"; then
  exit 0
fi

# tmux内かチェック
if [ -n "$TMUX" ]; then
  exit 0
fi

# tmux new-session等でラップされている場合はOK
if echo "$CMD" | grep -qE '^[[:space:]]*(tmux|screen)\s'; then
  exit 0
fi

# バックグラウンド実行（& 付き）の場合はOK
if echo "$CMD" | grep -qE '&\s*$'; then
  exit 0
fi

# standard: 警告のみ（ブロックしない）
echo '[Hook] WARNING: devサーバーはtmux内での実行を推奨します' >&2
echo '[Hook] 使い方: tmux new-session -d -s dev "npm run dev" && tmux attach -t dev' >&2
echo '[Hook] または: nohup npm run dev &' >&2

exit 0
