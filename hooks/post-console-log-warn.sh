#!/bin/bash
# post-console-log-warn.sh
# PostToolUse: 編集されたJS/TSファイルにconsole.logがあれば警告
# テストファイル・設定ファイル・scripts/は除外

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')

case "$TOOL" in
  Edit|Write|MultiEdit) ;;
  *) exit 0 ;;
esac

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')
if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# JS/TSファイルのみ対象
case "$FILE_PATH" in
  *.ts|*.tsx|*.js|*.jsx) ;;
  *) exit 0 ;;
esac

# テスト・設定・スクリプト系は除外
case "$FILE_PATH" in
  *.test.*|*.spec.*|*.config.*|*/scripts/*|*/__tests__/*|*/__mocks__/*|*/test/*) exit 0 ;;
esac

if [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

# console.logを検出
MATCHES=$(grep -n 'console\.log' "$FILE_PATH" 2>/dev/null | head -5)

if [ -n "$MATCHES" ]; then
  echo "[Hook] WARNING: console.log が検出されました: $FILE_PATH" >&2
  echo "$MATCHES" | while IFS= read -r line; do
    echo "  $line" >&2
  done
  echo "[Hook] コミット前にconsole.logを削除してください" >&2
fi

exit 0
