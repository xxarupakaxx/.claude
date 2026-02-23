#!/bin/bash
# pre-compact-handover.sh
# コンテキスト圧縮前にセッション状態をHANDOVER.mdに保存する
# 05_log.md（作業ログ）+ トランスクリプト末尾を組み合わせて保存

INPUT=$(cat)
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // ""')
CWD=$(echo "$INPUT" | jq -r '.cwd // ""')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')

if [ -z "$CWD" ]; then
  exit 0
fi

# HANDOVER.md の保存先
HANDOVER_DIR="$CWD/.local"
mkdir -p "$HANDOVER_DIR"
HANDOVER_FILE="$HANDOVER_DIR/HANDOVER.md"

# 最新のメモリディレクトリを探す
MEMORY_BASE=""
for dir in "$CWD/.local/memory" "$CWD/memory"; do
  if [ -d "$dir" ]; then
    MEMORY_BASE="$dir"
    break
  fi
done

LATEST_DIR=""
if [ -n "$MEMORY_BASE" ]; then
  LATEST_DIR=$(find "$MEMORY_BASE" -maxdepth 1 -type d -name "[0-9]*" 2>/dev/null | sort -r | head -1)
fi

# HANDOVER.md を生成
{
  echo "# Session Handover"
  echo ""
  echo "> Auto-generated before context compaction"
  echo "> Session: $SESSION_ID"
  echo "> Generated: $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""

  # 05_log.md があれば含める（最も重要な情報源）
  if [ -n "$LATEST_DIR" ] && [ -f "$LATEST_DIR/05_log.md" ]; then
    echo "## Task Log (05_log.md)"
    echo ""
    echo "Memory directory: \`$LATEST_DIR\`"
    echo ""
    cat "$LATEST_DIR/05_log.md"
    echo ""
  fi

  # 30_plan.md があれば含める
  if [ -n "$LATEST_DIR" ] && [ -f "$LATEST_DIR/30_plan.md" ]; then
    echo "## Plan (30_plan.md)"
    echo ""
    cat "$LATEST_DIR/30_plan.md"
    echo ""
  fi

  # トランスクリプトの末尾から直近のやり取りを抽出
  if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
    echo "## Recent Conversation (last 50 entries)"
    echo ""
    echo '```'
    tail -50 "$TRANSCRIPT" 2>/dev/null | while IFS= read -r line; do
      ROLE=$(echo "$line" | jq -r '.role // .type // "unknown"' 2>/dev/null)
      # assistantとuserのメッセージのみ抽出
      if [ "$ROLE" = "assistant" ] || [ "$ROLE" = "user" ]; then
        CONTENT=$(echo "$line" | jq -r '
          if .message then .message[0:300]
          elif .content then
            if (.content | type) == "string" then .content[0:300]
            elif (.content | type) == "array" then (.content[] | select(.type == "text") | .text[0:300]) // "..."
            else "..."
            end
          else "..."
          end
        ' 2>/dev/null)
        if [ -n "$CONTENT" ] && [ "$CONTENT" != "..." ] && [ "$CONTENT" != "null" ]; then
          echo "[$ROLE]: $CONTENT"
          echo "---"
        fi
      fi
    done
    echo '```'
    echo ""
  fi

  echo "## Recovery Instructions"
  echo ""
  echo "- Read this file to restore context after compaction"
  echo "- Check the memory directory for detailed task files"
  echo "- Continue from the phase indicated in the task log above"

} > "$HANDOVER_FILE"

exit 0
