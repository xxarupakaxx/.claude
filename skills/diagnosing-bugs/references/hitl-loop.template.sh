#!/usr/bin/env bash
# HITL (Human-in-the-Loop) Diagnostic Loop Template
#
# AI完全自動化が難しい状況（本番アクセス、対話的UI、特殊環境）で使用。
# AIは「ループ設計」と「結果分析」を担当し、実行はユーザーが手で行う。
#
# 使い方:
#   1. このテンプレを複製: cp hitl-loop.template.sh /tmp/diagnose-XXX.sh
#   2. PROBE / EXPECT / NOTE を埋める
#   3. ユーザーが実行→出力をAIに貼り付け→AIが次のPROBEを設計
#
# 設計原則:
#   - 1サイクル30秒以内
#   - 1コマンドで観測完了
#   - 失敗/成功が機械判定可能（exit code or grep）

set -uo pipefail

############################################
# CONFIG（埋めること）
############################################

# 何を観測したいか（1行で）
PROBE_DESCRIPTION="例: prod-api の /users エンドポイントが timeout する条件を特定"

# 期待する正常な状態（grepパターン or exit code）
EXPECT_PATTERN="200 OK"

# 注意事項（破壊的操作、PII露出への警戒等）
NOTE="例: 本番DB に書き込みは行わない。レスポンスにメールアドレスが含まれる場合はマスクして報告"

############################################
# PROBE（埋めること: 1コマンドで観測完了させる）
############################################

run_probe() {
  # 例1: HTTP probe
  curl -sS -o /tmp/last-body.txt -w "STATUS=%{http_code} TIME=%{time_total}s\n" \
    "https://prod.example.com/api/users?id=123"

  # 例2: ログ確認（直近1分）
  # ssh prod-host "journalctl -u myapp --since '1 minute ago' | tail -50"

  # 例3: DB状態確認（READ ONLY）
  # psql -h prod-replica -U readonly -d app -c \
  #   "SELECT id, status, updated_at FROM jobs WHERE id = 123 ;"
}

############################################
# JUDGE（自動判定）
############################################

judge() {
  local output="$1"
  if echo "$output" | grep -q "$EXPECT_PATTERN"; then
    echo "[PASS] expected pattern found"
    return 0
  else
    echo "[FAIL] expected pattern not found"
    return 1
  fi
}

############################################
# MAIN
############################################

echo "=== HITL Diagnostic Loop ==="
echo "PROBE: $PROBE_DESCRIPTION"
echo "EXPECT: $EXPECT_PATTERN"
echo "NOTE: $NOTE"
echo "=============================="
echo

while true; do
  echo ">>> Running probe ($(date '+%H:%M:%S'))..."
  output=$(run_probe 2>&1)
  echo "$output"
  echo
  judge "$output" || true
  echo
  read -rp "[Enter] to retry / [c] to capture for AI / [q] to quit: " action
  case "$action" in
    c)
      ts=$(date '+%Y%m%d-%H%M%S')
      file="/tmp/diagnose-capture-$ts.txt"
      printf '%s\n' "$output" > "$file"
      echo "Captured to: $file"
      echo "→ この内容をAIに貼り付けて次の仮説を依頼してください"
      ;;
    q) exit 0 ;;
    *) ;;  # default: retry
  esac
done
