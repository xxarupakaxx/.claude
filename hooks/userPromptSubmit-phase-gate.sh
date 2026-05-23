#!/bin/bash
# userPromptSubmit-phase-gate.sh
# UserPromptSubmit: Phase 2 (計画) 未完での実装着手を警告 (exit 1, ブロックではない)
#
# 検出: 「実装」「コード書く」「ファイル作成」系のキーワードを含むユーザープロンプト
# 条件: 直近メモリディレクトリの 05_log.md に "## Phase 2: 計画完了" マーカーが無い
# 動作: exit 1 + stderr 警告 (blockではない、Claude側で判断可能)
#
# 例外:
# - 05_log.md 不在 → 軽量タスクとして素通り
# - CLAUDE_SKIP_PHASE_GATE=1 → 1セッションのみバイパス

INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt // ""')

if [ -z "$PROMPT" ]; then
  exit 0
fi

# 環境変数バイパス
if [ "$CLAUDE_SKIP_PHASE_GATE" = "1" ]; then
  exit 0
fi

# 「実装」系キーワード判定（過剰検知を避けるため、限定的に）
if ! echo "$PROMPT" | grep -qE '実装してください|実装して下さい|コード書いて|ファイル作成して|機能追加して|機能を追加して|ファイルを作って' ; then
  exit 0
fi

# 直近メモリディレクトリの 05_log.md 探索
LATEST_LOG=""
if [ -d "$HOME/.claude/.local/memory" ]; then
  LATEST_LOG=$(find "$HOME/.claude/.local/memory" -name "05_log.md" -type f 2>/dev/null | xargs -I{} stat -f "%m {}" {} 2>/dev/null | sort -rn | head -1 | awk '{print $2}')
fi

# 05_log.md 不在 → 軽量タスクとみなして素通り (R003 残存リスクとして許容、CALIB で再評価)
if [ -z "$LATEST_LOG" ] || [ ! -f "$LATEST_LOG" ]; then
  exit 0
fi

# Phase 2 完了マーカーチェック
if grep -qE '^##\s*Phase 2:?\s*(計画完了|Plan完了|完了)' "$LATEST_LOG" 2>/dev/null; then
  exit 0
fi

# 警告 (exit 1)
cat >&2 <<EOF
[Phase Gate] 警告: 直近メモリディレクトリの 05_log.md に「Phase 2: 計画完了」マーカーが見つかりません。

検出ファイル: $LATEST_LOG

CLAUDE.md ワークフロー Phase 2 (計画) を完了してから実装に着手してください。
30_plan.md 作成 + deepening-plan + サブエージェントレビュー + User Validation Gate が必要です。

意図的にスキップする場合: CLAUDE_SKIP_PHASE_GATE=1 を環境変数に設定してください。
EOF

exit 1
