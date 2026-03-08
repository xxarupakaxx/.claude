#!/bin/bash
# stop-workflow-check.sh
# Claudeの応答完了時にワークフロー遵守をチェック
# 05_log.mdが存在し、レスポンス内のPhaseに対応する記録があるか確認

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

# Phase移行の検出と内容ベースの整合性チェック
# grepはファイルに直接実行（echo+pipeはマルチバイト文字で問題が出る）

# Phase 3（実装）完了を主張しているか
if echo "$LAST_MSG" | grep -qiE '(Phase 3.*完了|実装完了|実装が完了)'; then
  if ! grep -qE '(Phase 3|## .*実装|Step [0-9])' "$LOG_FILE"; then
    echo '{"decision": "block", "reason": "実装完了が検出されましたが、05_log.mdにPhase 3（実装）の記録がありません。実装内容を記録してから完了報告してください。"}'
    exit 0
  fi
fi

# Phase 4（品質確認）完了を主張しているか
if echo "$LAST_MSG" | grep -qiE '(Phase 4.*完了|品質確認完了|品質チェック.*通過|typecheck.*PASS)'; then
  if ! grep -qE '(Phase 4|PASS|typecheck|lint)' "$LOG_FILE"; then
    echo '{"decision": "block", "reason": "品質確認完了が検出されましたが、05_log.mdにPhase 4（品質確認）の記録がありません。チェック結果を記録してから完了報告してください。"}'
    exit 0
  fi
fi

# Phase 5（完了報告）を主張しているか
if echo "$LAST_MSG" | grep -qiE '(Phase 5.*完了|完了報告|タスク完了)'; then
  HAS_IMPL=$(grep -cE '(Phase 3|## .*実装|Step [0-9])' "$LOG_FILE")
  HAS_QA=$(grep -cE '(Phase 4|PASS|typecheck|lint)' "$LOG_FILE")
  if [ "$HAS_IMPL" -eq 0 ] || [ "$HAS_QA" -eq 0 ]; then
    echo '{"decision": "block", "reason": "完了報告が検出されましたが、05_log.mdにPhase 3（実装）またはPhase 4（品質確認）の記録が不足しています。各Phaseの内容を記録してから完了報告してください。"}'
    exit 0
  fi
fi

exit 0
