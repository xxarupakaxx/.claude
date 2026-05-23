# Hook Template Reference

`~/.claude/hooks/<name>.sh` の生成テンプレート集。`create-hook` スキルから参照される。

## 基本構造 (全 hook 共通)

```bash
#!/bin/bash
# <name>.sh
# <イベント名>: <目的を1行で>
# 入力: stdin に JSON
# 出力: stdout (Hook 内容次第) / stderr (警告) / exit code (0/1/2)

INPUT=$(cat)

# 必要なフィールド抽出 (jq)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // ""')

# ... ロジック ...

exit 0  # 0=正常, 1=警告 (Claude側で判断), 2=ブロック (PreToolUseで効果的)
```

## イベント別テンプレート

### PreToolUse (危険コマンドブロック等)

```bash
INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')
if [ "$TOOL" != "Bash" ]; then exit 0; fi

CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

if echo "$CMD" | grep -qE '<危険パターン>'; then
  echo '[Hook] BLOCKED: 理由' >&2
  exit 2
fi
exit 0
```

### PostToolUse (フォーマット・lint 等)

```bash
INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')
# matcher: Write|Edit|MultiEdit
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')
[ -z "$FILE" ] && exit 0

# 例: prettier 実行
case "$FILE" in
  *.ts|*.tsx) prettier --write "$FILE" 2>/dev/null ;;
esac
exit 0
```

### UserPromptSubmit (Phase ゲート等)

```bash
INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt // ""')

if echo "$PROMPT" | grep -qE '<キーワード>'; then
  # 警告 (exit 1) or ブロック (exit 2)
  echo "[Gate] 警告メッセージ" >&2
  exit 1
fi
exit 0
```

### SessionStart (コンテキスト復元等)

```bash
INPUT=$(cat)
MATCHER=$(echo "$INPUT" | jq -r '.matcher // ""')  # startup|compact|""

# 例: HANDOVER.md があれば読み込み
if [ -f "$HOME/.claude/.local/HANDOVER.md" ]; then
  echo "前回セッションの引継ぎ: $(head -3 ~/.claude/.local/HANDOVER.md)"
fi
exit 0
```

### Stop (作業終了処理)

```bash
INPUT=$(cat)
# Claude が応答を返した直後に起動
# 例: 作業ログを memory.db に保存

exit 0
```

### SubagentStop (サブエージェント完了)

```bash
INPUT=$(cat)
AGENT_NAME=$(echo "$INPUT" | jq -r '.task_name // .agent_name // ""')

# 例: 結果集約 or 通知
exit 0
```

### PreCompact (compaction 前)

```bash
INPUT=$(cat)
# 例: HANDOVER.md 生成
echo "compaction 前のスナップショット保存"
exit 0
```

### SessionEnd (セッション終了)

```bash
INPUT=$(cat)
# 例: 統計集計、cleanup 提案
exit 0
```

### Notification (権限プロンプト・elicitation時)

```bash
INPUT=$(cat)
MATCHER=$(echo "$INPUT" | jq -r '.matcher // ""')
# 例: Bark 通知
exit 0
```

## settings.json 登録例

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/<name>.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## ログ追記パターン (監査用)

```bash
LOG="$HOME/.claude/.local/hooks/log/<name>.jsonl"
mkdir -p "$(dirname "$LOG")"

jq -nc \
  --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg sid "$SESSION_ID" \
  --arg <other> "$OTHER" \
  '{timestamp: $ts, session_id: $sid, ...}' \
  >> "$LOG"
```

## Anti-Patterns

- ❌ stdout に長文を出す (Claude に prompt として認識される)
- ❌ exit 2 を PostToolUse で使う (効果なし、PreToolUse 専用)
- ❌ flock 前提 (macOS は flock 不在)
- ❌ シークレットを log にそのまま出す (redact 必須)
- ❌ session_id をキーにせず単一ファイルでカウンタ管理 (worktree並列で競合)
- ❌ stderr で巨大なメッセージ (短く、エラー時のみ)
