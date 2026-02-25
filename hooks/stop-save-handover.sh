#!/bin/bash
# stop-save-handover.sh
# Claude停止時にHANDOVER.mdを保存する（アクティブタスク時のみ）
# /clear前に最新状態を保持するため、Stop毎に更新

INPUT=$(cat)

# 無限ループ防止
ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
if [ "$ACTIVE" = "true" ]; then
  exit 0
fi

CWD=$(echo "$INPUT" | jq -r '.cwd // ""')
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // ""')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')

if [ -z "$CWD" ]; then
  exit 0
fi

# メモリディレクトリを探す
MEMORY_BASE=""
for dir in "$CWD/.local/memory" "$CWD/memory"; do
  if [ -d "$dir" ]; then
    MEMORY_BASE="$dir"
    break
  fi
done

# アクティブタスクがない場合はスキップ
if [ -z "$MEMORY_BASE" ]; then
  exit 0
fi

LATEST_DIR=$(find "$MEMORY_BASE" -maxdepth 1 -type d -name "[0-9]*" 2>/dev/null | sort -r | head -1)

# 05_log.mdが存在しない場合はスキップ（タスク非活性）
if [ -z "$LATEST_DIR" ] || [ ! -f "$LATEST_DIR/05_log.md" ]; then
  exit 0
fi

# HANDOVER.md を保存
HANDOVER_DIR="$CWD/.local"
mkdir -p "$HANDOVER_DIR"
HANDOVER_FILE="$HANDOVER_DIR/HANDOVER.md"

{
  echo "# Session Handover"
  echo ""
  echo "> Auto-generated on Stop (for /clear recovery)"
  echo "> Session: $SESSION_ID"
  echo "> Generated: $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""

  # 05_log.md
  if [ -f "$LATEST_DIR/05_log.md" ]; then
    echo "## Task Log (05_log.md)"
    echo ""
    echo "Memory directory: \`$LATEST_DIR\`"
    echo ""
    cat "$LATEST_DIR/05_log.md"
    echo ""
  fi

  # 30_plan.md
  if [ -f "$LATEST_DIR/30_plan.md" ]; then
    echo "## Plan (30_plan.md)"
    echo ""
    cat "$LATEST_DIR/30_plan.md"
    echo ""
  fi

  # トランスクリプトの末尾
  if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
    echo "## Recent Conversation (last 30 entries)"
    echo ""
    echo '```'
    tail -30 "$TRANSCRIPT" 2>/dev/null | while IFS= read -r line; do
      ROLE=$(echo "$line" | jq -r '.role // .type // "unknown"' 2>/dev/null)
      if [ "$ROLE" = "assistant" ] || [ "$ROLE" = "user" ]; then
        CONTENT=$(echo "$line" | jq -r '
          if .message then .message[0:200]
          elif .content then
            if (.content | type) == "string" then .content[0:200]
            elif (.content | type) == "array" then (.content[] | select(.type == "text") | .text[0:200]) // "..."
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
  echo "- Read this file to restore context after /clear"
  echo "- Check the memory directory for detailed task files"
  echo "- Continue from the phase indicated in the task log above"

} > "$HANDOVER_FILE"

exit 0
