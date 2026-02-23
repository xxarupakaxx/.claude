#!/bin/bash
# stop-workflow-check.sh
# Claudeの応答完了時にワークフロー遵守をチェック
# 05_log.mdが存在し、Phase移行時に更新されているか確認

INPUT=$(cat)

# 無限ループ防止（CRITICAL）
ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
if [ "$ACTIVE" = "true" ]; then
  exit 0
fi

CWD=$(echo "$INPUT" | jq -r '.cwd // ""')
LAST_MSG=$(echo "$INPUT" | jq -r '.last_assistant_message // ""')

if [ -z "$CWD" ] || [ -z "$LAST_MSG" ]; then
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

# タスクコンテキストにない場合はスキップ
if [ -z "$MEMORY_BASE" ]; then
  exit 0
fi

# 最新のメモリディレクトリを検索
LATEST_DIR=$(find "$MEMORY_BASE" -maxdepth 1 -type d -name "[0-9]*" 2>/dev/null | sort -r | head -1)

if [ -z "$LATEST_DIR" ]; then
  exit 0
fi

LOG_FILE="$LATEST_DIR/05_log.md"

# 05_log.md が存在しない場合
if [ ! -f "$LOG_FILE" ]; then
  # Phase関連のキーワードがあるときだけ警告
  if echo "$LAST_MSG" | grep -qiE '(Phase [0-5]|調査|計画|実装|品質|完了)'; then
    echo '{"decision": "block", "reason": "05_log.md が存在しません。タスク開始時にPhase 0でメモリディレクトリとログファイルを作成してください。パス: '"$LATEST_DIR"'/05_log.md"}'
    exit 0
  fi
  exit 0
fi

# Phase移行キーワードを検出
if echo "$LAST_MSG" | grep -qiE '(Phase [0-5].*完了|Phase [0-5].*移行|完了報告|品質確認完了|実装完了|計画承認|調査完了|次のPhase)'; then
  # 05_log.md の最終更新時刻をチェック（macOS/Linux対応）
  if [ "$(uname)" = "Darwin" ]; then
    MOD_TIME=$(stat -f %m "$LOG_FILE")
  else
    MOD_TIME=$(stat -c %Y "$LOG_FILE")
  fi
  NOW=$(date +%s)
  DIFF=$((NOW - MOD_TIME))

  # 5分以上更新されていない場合に警告
  if [ "$DIFF" -gt 300 ]; then
    echo "{\"decision\": \"block\", \"reason\": \"Phase移行が検出されましたが、05_log.mdが$(($DIFF / 60))分間更新されていません。現在のPhaseの作業内容を05_log.mdに記録してから次のPhaseに進んでください。\"}"
    exit 0
  fi
fi

exit 0
