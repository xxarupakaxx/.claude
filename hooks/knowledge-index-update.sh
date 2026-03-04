#!/bin/bash
# knowledge-index-update.sh
# 検索結果で参照されたファイルのref_countを更新

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // ""')
TOOL_OUTPUT=$(echo "$INPUT" | jq -r '.tool_output // ""')

if [ -z "$CWD" ] || [ "$CWD" = "null" ]; then
  exit 0
fi

# Git repoのトップレベルを取得
TOPLEVEL=$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null) || exit 0
MEMORY_DIR="$TOPLEVEL/.local"
INDEX_FILE="$MEMORY_DIR/index.json"

# index.jsonがなければ初期化
if [ ! -f "$INDEX_FILE" ]; then
  echo '{"files":{},"synonyms":{}}' > "$INDEX_FILE"
fi

# solutions/ または memories/ のパスを抽出してカウントアップ
TODAY=$(date +%Y-%m-%d)

# 出力からsolutions/またはmemories/のパスを抽出
PATHS=$(echo "$TOOL_OUTPUT" | grep -oE "(solutions|memories)/[a-zA-Z0-9_/-]+\.md" | sort -u)

if [ -z "$PATHS" ]; then
  exit 0
fi

# 各パスのref_countを更新
for path in $PATHS; do
  FULL_PATH="$MEMORY_DIR/$path"
  if [ -f "$FULL_PATH" ]; then
    # jqで更新
    jq --arg path "$path" --arg today "$TODAY" '
      .files[$path] //= {"ref_count": 0, "created": $today} |
      .files[$path].ref_count += 1 |
      .files[$path].last_accessed = $today
    ' "$INDEX_FILE" > "$INDEX_FILE.tmp" && mv "$INDEX_FILE.tmp" "$INDEX_FILE"
  fi
done

exit 0
