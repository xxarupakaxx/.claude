#!/bin/bash
# pre-dangerous-command-block.sh
# PreToolUse: 破壊的コマンドをブロック（exit 2でツール実行を阻止）
# 対象: rm -rf /, DROP TABLE/DATABASE, format/fdisk等

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')

if [ "$TOOL" != "Bash" ]; then
  exit 0
fi

CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

if [ -z "$CMD" ]; then
  exit 0
fi

# パターン1: rm -rf / (ルートディレクトリの再帰的削除)
if echo "$CMD" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive\s+--force|-[a-zA-Z]*f[a-zA-Z]*r)\s+/\s*$'; then
  echo '[Hook] BLOCKED: rm -rf / は実行できません' >&2
  exit 2
fi

# パターン2: rm -rf /* (ルート直下のワイルドカード削除)
if echo "$CMD" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive)\s+/\*'; then
  echo '[Hook] BLOCKED: rm -rf /* は実行できません' >&2
  exit 2
fi

# パターン3: rm -rf ~ (ホームディレクトリの再帰的削除)
if echo "$CMD" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive)\s+~/?\s*$'; then
  echo '[Hook] BLOCKED: ホームディレクトリの再帰的削除は実行できません' >&2
  exit 2
fi

# パターン4: SQL破壊系 (DROP TABLE/DATABASE)
if echo "$CMD" | grep -qiE '(DROP\s+(TABLE|DATABASE|SCHEMA)\s|TRUNCATE\s+TABLE\s|DELETE\s+FROM\s+\S+\s*;?\s*$)'; then
  echo '[Hook] BLOCKED: 破壊的SQLコマンドは直接実行できません。マイグレーションを使用してください' >&2
  exit 2
fi

# パターン5: ディスクフォーマット系
if echo "$CMD" | grep -qE '(mkfs\.|fdisk\s|dd\s+if=.+of=/dev/)'; then
  echo '[Hook] BLOCKED: ディスク操作コマンドは実行できません' >&2
  exit 2
fi

# パターン6: chmod 777 再帰的
if echo "$CMD" | grep -qE 'chmod\s+(-R\s+)?777\s+/'; then
  echo '[Hook] WARNING: chmod 777 はセキュリティリスクがあります' >&2
  exit 2
fi

# パターン7: git push --force to main/master
if echo "$CMD" | grep -qE 'git\s+push\s+.*--force.*\s+(main|master)'; then
  echo '[Hook] BLOCKED: main/masterへのforce pushは実行できません' >&2
  exit 2
fi

exit 0
