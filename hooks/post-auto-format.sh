#!/bin/bash
# post-auto-format.sh
# PostToolUse: Edit/Write後に自動フォーマットを実行
# biome.json → .prettierrc → deno.json の順で検出し、見つかったものを使用

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

# JS/TS/JSON/CSS系ファイルのみ対象
case "$FILE_PATH" in
  *.ts|*.tsx|*.js|*.jsx|*.json|*.css|*.scss|*.vue|*.svelte) ;;
  *) exit 0 ;;
esac

# ファイルが存在するか確認
if [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

PROJECT_DIR=$(dirname "$FILE_PATH")
# プロジェクトルートを探す（git root or package.json のある場所）
while [ "$PROJECT_DIR" != "/" ]; do
  if [ -f "$PROJECT_DIR/package.json" ] || [ -d "$PROJECT_DIR/.git" ]; then
    break
  fi
  PROJECT_DIR=$(dirname "$PROJECT_DIR")
done

if [ "$PROJECT_DIR" = "/" ]; then
  exit 0
fi

# フォーマッター検出と実行
FORMATTED=false

# 1. Biome
if [ -f "$PROJECT_DIR/biome.json" ] || [ -f "$PROJECT_DIR/biome.jsonc" ]; then
  if command -v npx >/dev/null 2>&1; then
    npx --yes @biomejs/biome format --write "$FILE_PATH" 2>/dev/null
    if [ $? -eq 0 ]; then
      FORMATTED=true
    fi
  fi
fi

# 2. Prettier (fallback)
if [ "$FORMATTED" = "false" ]; then
  if [ -f "$PROJECT_DIR/.prettierrc" ] || [ -f "$PROJECT_DIR/.prettierrc.js" ] || [ -f "$PROJECT_DIR/.prettierrc.json" ] || [ -f "$PROJECT_DIR/prettier.config.js" ] || [ -f "$PROJECT_DIR/prettier.config.mjs" ]; then
    if command -v npx >/dev/null 2>&1; then
      npx --yes prettier --write "$FILE_PATH" 2>/dev/null
      if [ $? -eq 0 ]; then
        FORMATTED=true
      fi
    fi
  fi
fi

# 3. Deno (fallback)
if [ "$FORMATTED" = "false" ]; then
  if [ -f "$PROJECT_DIR/deno.json" ] || [ -f "$PROJECT_DIR/deno.jsonc" ]; then
    if command -v deno >/dev/null 2>&1; then
      deno fmt "$FILE_PATH" 2>/dev/null
      FORMATTED=true
    fi
  fi
fi

exit 0
