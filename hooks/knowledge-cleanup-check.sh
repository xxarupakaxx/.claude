#!/bin/bash
# knowledge-cleanup-check.sh
# SessionEnd時に30日未参照・重複候補をチェックして報告

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // ""')

if [ -z "$CWD" ] || [ "$CWD" = "null" ]; then
  exit 0
fi

# Git repoのトップレベルを取得
TOPLEVEL=$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null) || exit 0
MEMORY_DIR="$TOPLEVEL/.local"
INDEX_FILE="$MEMORY_DIR/index.json"

if [ ! -f "$INDEX_FILE" ]; then
  exit 0
fi

TODAY=$(date +%Y-%m-%d)
THRESHOLD_DATE=$(date -v-30d +%Y-%m-%d 2>/dev/null || date -d "30 days ago" +%Y-%m-%d 2>/dev/null)

# 30日未参照のファイルを検出
STALE_FILES=$(jq -r --arg threshold "$THRESHOLD_DATE" '
  .files | to_entries[] |
  select(.value.last_accessed < $threshold or .value.last_accessed == null) |
  "\(.key) (last: \(.value.last_accessed // "never"))"
' "$INDEX_FILE" 2>/dev/null)

# 同一タグのファイル数をカウント（統合候補）
# solutions/内のファイルからタグを抽出してカウント
DUPLICATE_TAGS=""
if [ -d "$MEMORY_DIR/solutions" ]; then
  DUPLICATE_TAGS=$(find "$MEMORY_DIR/solutions" -name "*.md" -exec grep -h "^tags:" {} \; 2>/dev/null | \
    sed 's/tags:\s*\[//;s/\]//;s/,/\n/g' | \
    sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | \
    sort | uniq -c | sort -rn | \
    awk '$1 >= 3 {print $1 " files with tag: " $2}' | head -5)
fi

# 結果があれば報告
if [ -n "$STALE_FILES" ] || [ -n "$DUPLICATE_TAGS" ]; then
  echo ""
  echo "=== Knowledge Cleanup Suggestions ==="

  if [ -n "$STALE_FILES" ]; then
    echo ""
    echo "[Archive candidates - 30 days without access]"
    echo "$STALE_FILES" | head -10
  fi

  if [ -n "$DUPLICATE_TAGS" ]; then
    echo ""
    echo "[Merge candidates - similar topics]"
    echo "$DUPLICATE_TAGS"
  fi

  echo ""
  echo "Run /cleanup-knowledge to review and act on these suggestions."
fi

exit 0
