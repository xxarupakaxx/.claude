#!/bin/bash
# Stop hook: セッション終了時に失敗パターンを検出して候補ファイルに保存
# settings.json の Stop で呼び出される

SUGGEST_DIR="${HOME}/.claude/.local/harness-suggestions"
mkdir -p "$SUGGEST_DIR"

# セッションのトランスクリプトパスを推定
# Claude Code はプロジェクトディレクトリ配下に JSONL を保存する
PROJECT_DIR="${HOME}/.claude/projects"
if [ ! -d "$PROJECT_DIR" ]; then
  exit 0
fi

# 直近1時間以内に更新されたセッションファイルを探す
RECENT_SESSION=$(find "$PROJECT_DIR" -name "*.jsonl" -mmin -60 -type f 2>/dev/null | sort -t/ -k1 | tail -1)

if [ -z "$RECENT_SESSION" ] || [ ! -f "$RECENT_SESSION" ]; then
  exit 0
fi

# エラーパターンのカウント（軽量チェック）
ERROR_COUNT=$(grep -c '"error"' "$RECENT_SESSION" 2>/dev/null || echo 0)
RETRY_COUNT=$(grep -ci 'retry\|retrying\|again' "$RECENT_SESSION" 2>/dev/null || echo 0)
REPEATED_READ=$(grep -o '"Read"' "$RECENT_SESSION" 2>/dev/null | wc -l | tr -d ' ')

# 閾値判定: 重要な失敗パターンがある場合のみ記録
NEEDS_REVIEW=0
REASONS=""

if [ "$ERROR_COUNT" -gt 5 ]; then
  NEEDS_REVIEW=1
  REASONS="${REASONS}errors:${ERROR_COUNT} "
fi

if [ "$RETRY_COUNT" -gt 3 ]; then
  NEEDS_REVIEW=1
  REASONS="${REASONS}retries:${RETRY_COUNT} "
fi

if [ "$REPEATED_READ" -gt 50 ]; then
  NEEDS_REVIEW=1
  REASONS="${REASONS}excessive_reads:${REPEATED_READ} "
fi

if [ "$NEEDS_REVIEW" -eq 1 ]; then
  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  if command -v jq &>/dev/null; then
    jq -n \
      --arg ts "$TIMESTAMP" \
      --arg sess "$RECENT_SESSION" \
      --argjson err "$ERROR_COUNT" \
      --argjson ret "$RETRY_COUNT" \
      --argjson rd "$REPEATED_READ" \
      --arg reasons "$REASONS" \
      '{timestamp:$ts, session:$sess, errors:$err, retries:$ret, reads:$rd, reasons:$reasons, reviewed:false}' \
      > "${SUGGEST_DIR}/${TIMESTAMP}.json"
  else
    printf '{"timestamp":"%s","session":"%s","errors":%d,"retries":%d,"reads":%d,"reasons":"%s","reviewed":false}\n' \
      "$TIMESTAMP" "$(echo "$RECENT_SESSION" | sed 's/["\\]/\\&/g')" \
      "$ERROR_COUNT" "$RETRY_COUNT" "$REPEATED_READ" "$REASONS" \
      > "${SUGGEST_DIR}/${TIMESTAMP}.json"
  fi
fi
