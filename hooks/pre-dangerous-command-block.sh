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

# パターン8: git push --force-with-lease to main/master（より安全だがmain/masterは禁止）
if echo "$CMD" | grep -qE 'git\s+push\s+.*--force-with-lease.*\s+(main|master)\b'; then
  echo '[Hook] BLOCKED: main/masterへの--force-with-leaseも禁止です' >&2
  exit 2
fi

# パターン9: git reset --hard origin/main|master (リモート追従のhard reset)
if echo "$CMD" | grep -qE 'git\s+reset\s+--hard\s+(origin/)?(main|master)\b'; then
  echo '[Hook] BLOCKED: main/masterへのhard resetは禁止（明示的にユーザー承認が必要）' >&2
  exit 2
fi

# パターン10: git branch -D main|master / develop（保護ブランチの強制削除）
if echo "$CMD" | grep -qE 'git\s+branch\s+(-D|-d\s+--force|--delete\s+--force)\s+(main|master|develop)\b'; then
  echo '[Hook] BLOCKED: 保護ブランチ(main/master/develop)の強制削除は禁止' >&2
  exit 2
fi

# パターン11: git push --delete でリモートのmain/master削除
if echo "$CMD" | grep -qE 'git\s+push\s+\S+\s+(--delete|:)\s*(main|master)\b'; then
  echo '[Hook] BLOCKED: リモートmain/masterの削除は禁止' >&2
  exit 2
fi

# パターン12: git clean -fdx (untracked + .gitignore対象まで消す危険操作)
if echo "$CMD" | grep -qE 'git\s+clean\s+(-[a-zA-Z]*f[a-zA-Z]*d[a-zA-Z]*x|-[a-zA-Z]*f[a-zA-Z]*x[a-zA-Z]*d|-[a-zA-Z]*x[a-zA-Z]*f[a-zA-Z]*d|-[a-zA-Z]*x[a-zA-Z]*d[a-zA-Z]*f|-[a-zA-Z]*d[a-zA-Z]*f[a-zA-Z]*x|-[a-zA-Z]*d[a-zA-Z]*x[a-zA-Z]*f)\b'; then
  echo '[Hook] BLOCKED: git clean -fdx は.gitignore対象まで削除するため禁止（-fd までに留めてください）' >&2
  exit 2
fi

# パターン13: git filter-branch / filter-repo（履歴書き換え）
if echo "$CMD" | grep -qE 'git\s+(filter-branch|filter-repo)\b'; then
  echo '[Hook] BLOCKED: 履歴書き換え（filter-branch/filter-repo）は明示的承認が必要' >&2
  exit 2
fi

# パターン14: git config --global の user.* / safe.* 改変（CLAUDE.md「NEVER update the git config」）
if echo "$CMD" | grep -qE 'git\s+config\s+(--global|--system)\b'; then
  echo '[Hook] BLOCKED: git config --global/--system の変更は禁止（CLAUDE.md規約）' >&2
  exit 2
fi

# パターン15: git update-ref / symbolic-ref で main/master を直接書き換え
if echo "$CMD" | grep -qE 'git\s+(update-ref|symbolic-ref)\s+(refs/heads/)?(main|master)\b'; then
  echo '[Hook] BLOCKED: main/masterのref直接書き換えは禁止' >&2
  exit 2
fi

# パターン16: git reflog expire --expire=now --all（reflog全削除でリカバリ不可に）
if echo "$CMD" | grep -qE 'git\s+reflog\s+expire\s+.*--expire=now.*--all'; then
  echo '[Hook] BLOCKED: reflog全削除はリカバリ不可になるため禁止' >&2
  exit 2
fi

# パターン17: git commit --amend after push（明示メッセージで警告）
# ※確実な検出は困難なので、--no-verify との併用のみブロック
if echo "$CMD" | grep -qE 'git\s+commit\s+.*--amend.*--no-verify'; then
  echo '[Hook] BLOCKED: --amend と --no-verify の併用は禁止（フックスキップ＋履歴改変）' >&2
  exit 2
fi

# パターン18: git push --no-verify (フックスキップ)
if echo "$CMD" | grep -qE 'git\s+push\s+.*--no-verify\b'; then
  echo '[Hook] BLOCKED: git push --no-verify は禁止（フックをスキップしないこと）' >&2
  exit 2
fi

exit 0
