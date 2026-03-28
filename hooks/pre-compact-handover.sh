#!/bin/bash
# pre-compact-handover.sh
# コンテキスト圧縮前にセッション状態をHANDOVER.mdに保存する
# 05_log.md（作業ログ）+ 構造化セッション状態 + トランスクリプト末尾を組み合わせて保存

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

# 現在のPhaseを推定
CURRENT_PHASE="unknown"
if [ -n "$LATEST_DIR" ] && [ -f "$LATEST_DIR/05_log.md" ]; then
  if grep -qE 'Phase 5|完了報告' "$LATEST_DIR/05_log.md"; then
    CURRENT_PHASE="5 (完了報告)"
  elif grep -qE 'Phase 4|品質確認' "$LATEST_DIR/05_log.md"; then
    CURRENT_PHASE="4 (品質確認)"
  elif grep -qE 'Phase 3|実装' "$LATEST_DIR/05_log.md"; then
    CURRENT_PHASE="3 (実装)"
  elif grep -qE 'Phase 2\.5|Acceptance|Sprint Contract|checkpoint' "$LATEST_DIR/05_log.md"; then
    CURRENT_PHASE="2.5 (Acceptance Criteria)"
  elif grep -qE 'Phase 2|計画' "$LATEST_DIR/05_log.md"; then
    CURRENT_PHASE="2 (計画)"
  elif grep -qE 'Phase 1|調査' "$LATEST_DIR/05_log.md"; then
    CURRENT_PHASE="1 (調査)"
  elif grep -qE 'Phase 0|準備' "$LATEST_DIR/05_log.md"; then
    CURRENT_PHASE="0 (準備)"
  fi
fi

# HANDOVER.md を生成
{
  echo "# Session Handover"
  echo ""
  echo "> Auto-generated before context compaction"
  echo "> Session: $SESSION_ID"
  echo "> Generated: $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""

  # 構造化セッション状態
  echo "## Session State"
  echo ""
  echo "- **Current Phase**: $CURRENT_PHASE"
  if [ -n "$LATEST_DIR" ]; then
    echo "- **Memory Directory**: \`$LATEST_DIR\`"
  fi

  # 次のアクションを推定
  echo "- **Next Action**: "
  case "$CURRENT_PHASE" in
    "0 (準備)") echo "  Phase 1（調査）を開始" ;;
    "1 (調査)") echo "  調査結果をまとめ、GO/NO-GO判定を行う" ;;
    "2 (計画)") echo "  計画のサブエージェントレビュー→ユーザー承認" ;;
    "2.5 (Acceptance Criteria)") echo "  Phase 3（実装）を開始" ;;
    "3 (実装)") echo "  残タスクの実装を続行→Phase 4へ" ;;
    "4 (品質確認)") echo "  レビュー指摘の修正→Phase 5へ" ;;
    "5 (完了報告)") echo "  Phase 5.5（Compound）を実行" ;;
    *) echo "  05_log.mdを確認して状態を復元" ;;
  esac
  echo ""

  # checkpoint.mdがあれば含める
  if [ -n "$LATEST_DIR" ] && [ -f "$LATEST_DIR/checkpoint.md" ]; then
    echo "## Acceptance Criteria (checkpoint.md)"
    echo ""
    head -50 "$LATEST_DIR/checkpoint.md"
    echo ""
  fi

  # 05_log.md があれば含める（最も重要な情報源）
  if [ -n "$LATEST_DIR" ] && [ -f "$LATEST_DIR/05_log.md" ]; then
    echo "## Task Log (05_log.md)"
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
  echo "1. Read this file to restore context after compaction"
  echo "2. Check the memory directory for detailed task files"
  echo "3. Resume from **Phase $CURRENT_PHASE** (see Next Action above)"
  echo "4. If checkpoint.md exists, use \`/verify\` to check acceptance criteria status"

} > "$HANDOVER_FILE"

exit 0
