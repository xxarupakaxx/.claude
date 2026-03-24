#!/bin/bash
# post-typescript-check.sh
# PostToolUse: .ts/.tsx編集後にtsc --noEmitを実行（型エラーの早期検出）
# tsconfig.jsonが存在するプロジェクトでのみ実行

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

# TypeScriptファイルのみ対象
case "$FILE_PATH" in
  *.ts|*.tsx) ;;
  *) exit 0 ;;
esac

# .d.tsは除外
case "$FILE_PATH" in
  *.d.ts) exit 0 ;;
esac

if [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

# プロジェクトルートを探す
PROJECT_DIR=$(dirname "$FILE_PATH")
while [ "$PROJECT_DIR" != "/" ]; do
  if [ -f "$PROJECT_DIR/tsconfig.json" ]; then
    break
  fi
  PROJECT_DIR=$(dirname "$PROJECT_DIR")
done

# tsconfig.jsonが見つからなければスキップ
if [ ! -f "$PROJECT_DIR/tsconfig.json" ]; then
  exit 0
fi

# tsc --noEmit を実行（タイムアウト15秒）
if command -v npx >/dev/null 2>&1; then
  RESULT=$(cd "$PROJECT_DIR" && timeout 15 npx tsc --noEmit 2>&1 | grep -E "error TS" | head -5)
  if [ -n "$RESULT" ]; then
    echo "[Hook] TypeScript型エラー検出:" >&2
    echo "$RESULT" | while IFS= read -r line; do
      echo "  $line" >&2
    done
    ERROR_COUNT=$(cd "$PROJECT_DIR" && timeout 15 npx tsc --noEmit 2>&1 | grep -c "error TS" || echo "?")
    if [ "$ERROR_COUNT" -gt 5 ]; then
      echo "  ... 他 $((ERROR_COUNT - 5)) 件のエラー" >&2
    fi
  fi
fi

exit 0
