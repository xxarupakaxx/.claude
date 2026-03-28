#!/bin/bash
# pre-strategic-compact-suggest.sh
# PreToolUse: Edit/Writeの回数をカウントし、閾値を超えたら/compact提案
# Phase完了キーワードも検出し、論理的なブレークポイントでcompactを促す

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')

# Edit/Writeのみカウント
case "$TOOL" in
  Edit|Write|MultiEdit) ;;
  *) exit 0 ;;
esac

CWD=$(echo "$INPUT" | jq -r '.cwd // ""')
if [ -z "$CWD" ]; then
  exit 0
fi

# カウンターファイル
COUNTER_DIR="${TMPDIR:-/tmp}/claude-compact-counter"
mkdir -p "$COUNTER_DIR"

# CWDのハッシュをキーにする
DIR_HASH=$(echo "$CWD" | md5 2>/dev/null || echo "$CWD" | md5sum 2>/dev/null | cut -d' ' -f1)
COUNTER_FILE="$COUNTER_DIR/$DIR_HASH"

# カウンターを読み込み・インクリメント
COUNT=0
if [ -f "$COUNTER_FILE" ]; then
  COUNT=$(cat "$COUNTER_FILE" 2>/dev/null || echo 0)
fi
COUNT=$((COUNT + 1))
echo "$COUNT" > "$COUNTER_FILE"

# 閾値: 50回でリマインダー、100回で強い推奨
SUGGEST_THRESHOLD=50
STRONG_THRESHOLD=100

if [ "$COUNT" -eq "$SUGGEST_THRESHOLD" ]; then
  echo "[Hook] HINT: ${COUNT}回の編集操作を検出しました。Phase完了後など論理的なブレークポイントで /compact の実行を検討してください" >&2
elif [ "$COUNT" -eq "$STRONG_THRESHOLD" ]; then
  echo "[Hook] RECOMMEND: ${COUNT}回の編集操作を検出。コンテキスト品質維持のため /compact を強く推奨します" >&2
  echo "0" > "$COUNTER_FILE"  # リセット
fi

exit 0
