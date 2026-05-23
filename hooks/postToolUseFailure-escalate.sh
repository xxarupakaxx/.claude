#!/bin/bash
# postToolUseFailure-escalate.sh
# PostToolUse (failure case): ビルドエラー・テスト失敗が連続3回続いた場合にエスカレーション
#
# 検出: tool が失敗(non-zero exit)した場合
# 動作:
# - 連続失敗カウントをファイルで管理
# - 3回連続で同種の失敗が続いたら Bark 通知 + stderr 警告
# - 成功時にカウンターリセット

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exitCode // .exitCode // 0')

# 対象ツール: Bash (ビルド/テスト想定)
if [ "$TOOL" != "Bash" ]; then
  exit 0
fi

STATE_DIR="$HOME/.claude/.local/hooks/state"
mkdir -p "$STATE_DIR" 2>/dev/null
COUNTER_FILE="$STATE_DIR/postToolUseFailure_counter"

if [ "$EXIT_CODE" = "0" ]; then
  # 成功時: リセット
  rm -f "$COUNTER_FILE" 2>/dev/null
  exit 0
fi

# 失敗時: カウントアップ
CURRENT=0
if [ -f "$COUNTER_FILE" ]; then
  CURRENT=$(cat "$COUNTER_FILE" 2>/dev/null || echo 0)
fi
CURRENT=$((CURRENT + 1))
echo "$CURRENT" > "$COUNTER_FILE"

# 3回連続でエスカレーション
if [ "$CURRENT" -ge 3 ]; then
  cat >&2 <<EOF
[Escalate] ⚠️ Bash ツール失敗が ${CURRENT}回連続しています。

考えられる対応:
1. エラーメッセージを精読し根本原因を特定
2. /diagnosing-bugs スキルで体系的にデバッグ
3. ユーザーに状況報告して判断を仰ぐ

このループから抜け出すために一度立ち止まることを推奨します。
EOF

  # Bark 通知 (環境変数があれば)
  if [ -n "$BARK_DEVICE_KEY" ]; then
    bash "$HOME/.claude/hooks/bark-notify.sh" <<< "{\"title\":\"Build Failure x${CURRENT}\",\"body\":\"連続失敗中\"}" 2>/dev/null || true
  fi
fi

exit 0
