---
name: create-hook
description: イベント名と目的から `~/.claude/hooks/<name>.sh` の安全な雛形を作る。Hook追加、イベント別のstdin JSON処理、exit code、settings.json登録例の依頼に使う。
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion
---

# Create Hook

Claude Code Hookの雛形を生成するメタスキル。対象Hookの既存実装を確認してから、指定されたscopeだけを書き出す。Hookの有効化やsettings変更は自動で行わず、登録例を返す。

## 対象と入力

対応イベントは `PreToolUse`、`PostToolUse`、`UserPromptSubmit`、`SessionStart`、`SessionEnd`、`Stop`、`SubagentStop`、`PreCompact`、`Notification`。

| event | 主なstdin JSON | exit 2 |
| --- | --- | --- |
| `PreToolUse` | `tool_name`, `tool_input` | ツール実行をblock |
| `PostToolUse` | `tool_name`, `tool_input`, `tool_response` | 後続処理をblock |
| `UserPromptSubmit` | `prompt`, `cwd` | prompt処理を停止 |
| `SessionStart` / `SessionEnd` | `session_id`, `cwd` | — |
| `Stop` | `last_assistant_message`, `stop_hook_active` | blockして再実行 |
| `SubagentStop` | `subagent_type`, `result`, `stop_hook_active` | blockして再実行 |
| `PreCompact` | `transcript`抜粋 | — |
| `Notification` | `message` | — |

`/create-hook <event> <目的>` または自然言語の依頼を受けたら、対象tool/matcher、blockか通知だけか、ログ要否を確定する。不明点で挙動が変わる場合だけAskUserQuestionを使う。`~/.claude/hooks/*.sh` をGlobで調べ、nameと処理の衝突を避ける。

## 生成手順

1. イベント、目的、matcher、出力、ログ範囲、失敗時の扱いを短く決める。
2. `references/hook-templates.md` から該当イベントの雛形だけを読む。
3. 命名は `pre-*`、`post-*`、`stop-*`、`session-start-*`、`session-end-*`、`pre-compact-*` などeventが分かるprefixと役割を組み合わせ、既存pathと衝突させない。
4. `~/.claude/hooks/<name>.sh` に、目的に必要な最小コードを書き出す。

最低限の骨格は次のとおり。不要な入力抽出・重い処理・ログは追加しない。

```bash
#!/bin/bash
# <name>.sh — <event>: <目的>
# stdin: JSON / exit 0=continue, 1=warning, 2=block

INPUT=$(cat)

# Stop/SubagentStop only: prevent recursive execution
ACTIVE=$(printf '%s' "$INPUT" | jq -r '.stop_hook_active // false')
[ "$ACTIVE" = "true" ] && exit 0

TOOL=$(printf '%s' "$INPUT" | jq -r '.tool_name // ""')
CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // ""')
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // ""')

# Ignore unmatched tools/events early.
[ "$TOOL" != "Bash" ] && exit 0

if printf '%s' "$CMD" | grep -qE '<target pattern>'; then
  echo "[Hook] BLOCKED: <reason>" >&2
  exit 2
fi
exit 0
```

Stop/SubagentStopでは `stop_hook_active` を最初に確認する。stdinは `INPUT=$(cat)` で一度読み、`jq`で抽出する。対象外は早期 `exit 0`。PreToolUse/PostToolUseのstdoutを汚さず、診断はstderrまたはファイルへ出す。

## exit codeとログ

| code | 意味 |
| --- | --- |
| `0` | 続行 |
| `1` | 警告（stderrを表示） |
| `2` | block。PreToolUseではツール実行を止め、Stop系では再実行を要求 |

Stop/SubagentStopでblockする場合はstdoutへ `{"decision":"block","reason":"..."}` を出す。ログが必要な場合だけ `~/.claude/.local/hooks/log/<name>.jsonl` へJSON Linesでappendし、timestamp・session・必要な値だけを記録する。値は`jq -nc --arg`でescapeする。macOSの既存環境にflockがなければPOSIX appendを使い、機密情報はログへ書かない。

## settings登録と完了

settings.jsonは自動編集しない。ユーザーへ、matcherに合う絶対または `$CLAUDE_PROJECT_DIR` 基準のcommandを登録する例を返す。

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/<name>.sh" }
        ]
      }
    ]
  }
}
```

ユーザー設定なら `~/.claude/hooks/<name>.sh` を指定する。登録前に対象event・matcher・block挙動を確認し、実行権限が必要なら次を案内する。

```bash
chmod +x ~/.claude/hooks/<name>.sh
```

## 不合格条件

- `stop_hook_active` を見ずにStop系Hookを作る。
- 対象外のtoolまで処理する、stdoutへログを出す、通知だけなのにexit 2を返す。
- stdin JSONの未検証値をshellへ未引用で渡す、ログへ秘密情報を保存する。
- settingsへ相対pathを登録する、既存Hookとnameを衝突させる、目的外の自動処理を足す。

雛形のevent別の入力・応答仕様は `references/hook-templates.md` を参照する。関連するメタスキルは `create-skill`、`create-subagent`、`create-mcp-server`、settings更新は `update-config`。
