#!/bin/bash
# stop-console-log-audit.sh
# Stop: 各応答完了時に全変更ファイルのconsole.logを監査
# git diffで変更されたJS/TSファイルを対象とし、テスト系は除外

INPUT=$(cat)

# 無限ループ防止
ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
if [ "$ACTIVE" = "true" ]; then
  exit 0
fi

CWD=$(echo "$INPUT" | jq -r '.cwd // ""')

if [ -z "$CWD" ] || [ ! -d "$CWD/.git" ]; then
  exit 0
fi

# 変更されたJS/TSファイルを取得（staged + unstaged）
MODIFIED_FILES=$(cd "$CWD" && git diff --name-only HEAD 2>/dev/null; cd "$CWD" && git diff --name-only --cached 2>/dev/null)

if [ -z "$MODIFIED_FILES" ]; then
  exit 0
fi

FOUND_FILES=""

echo "$MODIFIED_FILES" | sort -u | while IFS= read -r file; do
  # JS/TSのみ
  case "$file" in
    *.ts|*.tsx|*.js|*.jsx) ;;
    *) continue ;;
  esac
  # テスト・設定・スクリプト除外
  case "$file" in
    *.test.*|*.spec.*|*.config.*|*/scripts/*|*/__tests__/*|*/__mocks__/*) continue ;;
  esac

  FULL_PATH="$CWD/$file"
  if [ -f "$FULL_PATH" ]; then
    COUNT=$(grep -c 'console\.log' "$FULL_PATH" 2>/dev/null || echo 0)
    if [ "$COUNT" -gt 0 ]; then
      if [ -z "$FOUND_FILES" ]; then
        echo "[Hook] console.log 残存チェック:" >&2
        FOUND_FILES="found"
      fi
      echo "  $file: ${COUNT}件" >&2
    fi
  fi
done

exit 0
