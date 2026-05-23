#!/bin/bash
# pre-dangerous-command-block.sh
# PreToolUse: 破壊的コマンドをブロック（exit 2でツール実行を阻止）
# 対象: rm -rf /, DROP TABLE/DATABASE, format/fdisk等
#
# WU-1 拡張 (2026-05-24):
# - blocked.jsonl ロギング
# - /hardgate-disable によるTTL付きバイパス

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')

if [ "$TOOL" != "Bash" ]; then
  exit 0
fi

CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

if [ -z "$CMD" ]; then
  exit 0
fi

# ========== Helper Functions ==========

LOG_DIR="$HOME/.claude/.local/hooks/log"
STATE_DIR="$HOME/.claude/.local/hooks/state"
BYPASS_FILE="$STATE_DIR/hardgate_bypass.json"
BLOCKED_LOG="$LOG_DIR/blocked.jsonl"

mkdir -p "$LOG_DIR" "$STATE_DIR" 2>/dev/null

# バイパスチェック: hardgate_bypass.json があり expires_at > now なら BYPASS=1
# Hard cap: issued_at から 3600秒 (1時間) を超える bypass は無効化 (security CRITICAL C2)
BYPASS=0
BYPASS_REASON=""
BYPASS_MAX_TTL=3600
if [ -f "$BYPASS_FILE" ]; then
  EXPIRES_AT=$(jq -r '.expires_at // 0' "$BYPASS_FILE" 2>/dev/null)
  ISSUED_AT=$(jq -r '.issued_at // 0' "$BYPASS_FILE" 2>/dev/null)
  NOW=$(date +%s)
  # Hard cap チェック
  if [ -n "$ISSUED_AT" ] && [ "$ISSUED_AT" -gt 0 ] 2>/dev/null; then
    REQUESTED_TTL=$((EXPIRES_AT - ISSUED_AT))
    if [ "$REQUESTED_TTL" -gt "$BYPASS_MAX_TTL" ] 2>/dev/null; then
      echo "[Hook] WARNING: bypass TTL ($REQUESTED_TTL s) > max ($BYPASS_MAX_TTL s). Bypass無視" >&2
      rm -f "$BYPASS_FILE" 2>/dev/null
      EXPIRES_AT=0
    fi
  fi
  if [ -n "$EXPIRES_AT" ] && [ "$EXPIRES_AT" -gt "$NOW" ] 2>/dev/null; then
    BYPASS=1
    BYPASS_REASON=$(jq -r '.reason // "no reason"' "$BYPASS_FILE" 2>/dev/null)
  else
    # 期限切れ → 自動削除
    rm -f "$BYPASS_FILE" 2>/dev/null
  fi
fi

# シークレット redaction (security CRITICAL C1)
# - URL中の認証情報 (https://user:PASS@host)
# - 長すぎる CMD は 200 文字でtruncate
redact_secrets() {
  local s="$1"
  # https?://user:pass@host → https://user:***@host
  s=$(echo "$s" | sed -E 's#(https?://[^:/[:space:]]+):[^@[:space:]]+@#\1:***REDACTED***@#g')
  # truncate
  if [ ${#s} -gt 200 ]; then
    s="${s:0:200}...[truncated]"
  fi
  printf '%s' "$s"
}

# JSON 1行を blocked.jsonl に flock で排他追記
log_block() {
  local pattern_id="$1"
  local message="$2"
  local timestamp
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  local session_id
  session_id=$(echo "$INPUT" | jq -r '.session_id // ""')
  local bypass_used
  if [ "$BYPASS" = "1" ]; then bypass_used="true"; else bypass_used="false"; fi
  local bypass_reason_json
  if [ -n "$BYPASS_REASON" ]; then
    bypass_reason_json=$(jq -nc --arg r "$BYPASS_REASON" '$r')
  else
    bypass_reason_json="null"
  fi
  local cmd_redacted
  cmd_redacted=$(redact_secrets "$CMD")
  # 全フィールドを jq で一度に組み立て (log injection 対策)
  jq -nc \
    --arg ts "$timestamp" \
    --arg sid "$session_id" \
    --arg pid "$pattern_id" \
    --arg msg "$message" \
    --arg cmd "$cmd_redacted" \
    --arg bu "$bypass_used" \
    --arg br "$BYPASS_REASON" \
    '{
      timestamp: $ts,
      session_id: $sid,
      pattern_id: $pid,
      message: $msg,
      command: $cmd,
      bypass_used: ($bu == "true"),
      bypass_reason: (if $br == "" then null else $br end)
    }' >> "$BLOCKED_LOG"
}

# パターンマッチ時の共通処理
# usage: try_block <pattern_id> <regex> <user_message>
try_block() {
  local pattern_id="$1"
  local regex="$2"
  local message="$3"
  if echo "$CMD" | grep -qE "$regex"; then
    log_block "$pattern_id" "$message"
    if [ "$BYPASS" = "1" ]; then
      echo "[Hook] BYPASS (reason: $BYPASS_REASON): $message" >&2
      return 1  # bypass: don't block but log
    fi
    echo "[Hook] BLOCKED: $message" >&2
    exit 2
  fi
}

# SQL系は -qiE (大文字小文字無視)
try_block_i() {
  local pattern_id="$1"
  local regex="$2"
  local message="$3"
  if echo "$CMD" | grep -qiE "$regex"; then
    log_block "$pattern_id" "$message"
    if [ "$BYPASS" = "1" ]; then
      echo "[Hook] BYPASS (reason: $BYPASS_REASON): $message" >&2
      return 1
    fi
    echo "[Hook] BLOCKED: $message" >&2
    exit 2
  fi
}

# ========== Pattern Matchers ==========

# パターン1: rm -rf / (ルートディレクトリの再帰的削除)
try_block "rm-rf-root" 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive\s+--force|-[a-zA-Z]*f[a-zA-Z]*r)\s+/\s*$' \
  'rm -rf / は実行できません'

# パターン2: rm -rf /* (ルート直下のワイルドカード削除)
try_block "rm-rf-rootstar" 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive)\s+/\*' \
  'rm -rf /* は実行できません'

# パターン3: rm -rf ~ (ホームディレクトリの再帰的削除)
try_block "rm-rf-home" 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive)\s+~/?\s*$' \
  'ホームディレクトリの再帰的削除は実行できません'

# パターン4: SQL破壊系 (DROP TABLE/DATABASE)
try_block_i "sql-destructive" '(DROP\s+(TABLE|DATABASE|SCHEMA)\s|TRUNCATE\s+TABLE\s|DELETE\s+FROM\s+\S+\s*;?\s*$)' \
  '破壊的SQLコマンドは直接実行できません。マイグレーションを使用してください'

# パターン5: ディスクフォーマット系
try_block "disk-format" '(mkfs\.|fdisk\s|dd\s+if=.+of=/dev/)' \
  'ディスク操作コマンドは実行できません'

# パターン6: chmod 777 再帰的
try_block "chmod-777" 'chmod\s+(-R\s+)?777\s+/' \
  'chmod 777 はセキュリティリスクがあります'

# パターン7: git push --force to main/master
try_block "git-push-force-main" 'git\s+push\s+.*--force.*\s+(main|master)' \
  'main/masterへのforce pushは実行できません'

# パターン8: git push --force-with-lease to main/master
try_block "git-push-force-with-lease-main" 'git\s+push\s+.*--force-with-lease.*\s+(main|master)\b' \
  'main/masterへの--force-with-leaseも禁止です'

# パターン9: git reset --hard origin/main|master
try_block "git-reset-hard-main" 'git\s+reset\s+--hard\s+(origin/)?(main|master)\b' \
  'main/masterへのhard resetは禁止（明示的にユーザー承認が必要）'

# パターン10: git branch -D main|master / develop
try_block "git-branch-delete-protected" 'git\s+branch\s+(-D|-d\s+--force|--delete\s+--force)\s+(main|master|develop)\b' \
  '保護ブランチ(main/master/develop)の強制削除は禁止'

# パターン11: git push --delete でリモートのmain/master削除
try_block "git-push-delete-main" 'git\s+push\s+\S+\s+(--delete|:)\s*(main|master)\b' \
  'リモートmain/masterの削除は禁止'

# パターン12: git clean -fdx
try_block "git-clean-fdx" 'git\s+clean\s+(-[a-zA-Z]*f[a-zA-Z]*d[a-zA-Z]*x|-[a-zA-Z]*f[a-zA-Z]*x[a-zA-Z]*d|-[a-zA-Z]*x[a-zA-Z]*f[a-zA-Z]*d|-[a-zA-Z]*x[a-zA-Z]*d[a-zA-Z]*f|-[a-zA-Z]*d[a-zA-Z]*f[a-zA-Z]*x|-[a-zA-Z]*d[a-zA-Z]*x[a-zA-Z]*f)\b' \
  'git clean -fdx は.gitignore対象まで削除するため禁止（-fd までに留めてください）'

# パターン13: git filter-branch / filter-repo
try_block "git-filter" 'git\s+(filter-branch|filter-repo)\b' \
  '履歴書き換え（filter-branch/filter-repo）は明示的承認が必要'

# パターン14: git config --global / --system
try_block "git-config-global" 'git\s+config\s+(--global|--system)\b' \
  'git config --global/--system の変更は禁止（CLAUDE.md規約）'

# パターン15: git update-ref / symbolic-ref で main/master 直接書き換え
try_block "git-update-ref-main" 'git\s+(update-ref|symbolic-ref)\s+(refs/heads/)?(main|master)\b' \
  'main/masterのref直接書き換えは禁止'

# パターン16: git reflog expire --expire=now --all
try_block "git-reflog-expire-all" 'git\s+reflog\s+expire\s+.*--expire=now.*--all' \
  'reflog全削除はリカバリ不可になるため禁止'

# パターン17: git commit --amend --no-verify
try_block "git-amend-no-verify" 'git\s+commit\s+.*--amend.*--no-verify' \
  '--amend と --no-verify の併用は禁止（フックスキップ＋履歴改変）'

# パターン18: git push --no-verify
try_block "git-push-no-verify" 'git\s+push\s+.*--no-verify\b' \
  'git push --no-verify は禁止（フックをスキップしないこと）'

exit 0
