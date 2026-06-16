---
name: create-hook
description: イベント名 + 目的から ~/.claude/hooks/<name>.sh 雛形を生成するメタスキル。PreToolUse/PostToolUse/UserPromptSubmit/SessionStart/SessionEnd/Stop/SubagentStop/PreCompact/Notification の各イベントに対応。shebang・JSON入力受け取り（INPUT=$(cat)）・jq抽出テンプレ・exit code（0/1/2）使い分け・settings.json登録例・ログ追記パターンを含む雛形を生成。使用タイミング: (1) 新しいHookを追加したいとき、(2) /create-hook <イベント> <目的> 実行時、(3) 「Hookを作って」「PreToolUse Hook追加」「Stop時に〇〇したい」等の依頼時。create-skill 派生のメタスキル。
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion
---

# Create Hook

イベント名 + 目的から `~/.claude/hooks/<name>.sh` 雛形を生成するメタスキル。

## 既存設定との関係

- **settings.json**: Hook を有効化するために最終的に登録する
- **既存 Hook**: `~/.claude/hooks/*.sh` を Glob で確認し命名・パターン重複を避ける
- **create-skill / create-subagent**: 姉妹メタスキル

## 対応イベントと用途

| イベント | 入力 JSON 主要フィールド | exit 2 の意味 | 典型用途 |
|---------|---------------------------|-------------|---------|
| `PreToolUse` | `tool_name`, `tool_input` | ツール実行ブロック | 破壊的コマンド阻止・権限制御 |
| `PostToolUse` | `tool_name`, `tool_input`, `tool_response` | 後続処理ブロック | 自動 lint・format・型チェック |
| `UserPromptSubmit` | `prompt`, `cwd` | プロンプト処理停止 | Phase gate・PR モード判定 |
| `SessionStart` | `session_id`, `cwd` | — | コンテキスト注入・symlink 作成 |
| `SessionEnd` | `session_id`, `cwd` | — | 統計集計・cleanup 提案 |
| `Stop` | `last_assistant_message`, `stop_hook_active` | block + 再実行 | ワークフロー遵守・HANDOVER 保存 |
| `SubagentStop` | `subagent_type`, `result` | block + 再実行 | サブエージェント結果集約 |
| `PreCompact` | `transcript` 抜粋 | — | HANDOVER.md 書き出し |
| `Notification` | `message` | — | 外部通知（Slack/Bark） |

## ワークフロー

### Step 1: 要件パース

```
入力: /create-hook PostToolUse Edit/Write後にprettier自動実行
→ event: PostToolUse
→ matcher: Edit|Write
→ 名称候補: post-auto-format.sh
```

不明点があれば AskUserQuestion で確認:
- 対象 tool（`matcher` フィルタ）
- ブロックすべきか通知のみか
- ログ出力先

### Step 2: イベント別テンプレ選択

`Read references/hook-templates.md` から該当イベントの雛形を取得。
本SKILL内では骨格のみ提示（次節）。

### Step 3: 命名規約

- prefix で event を表す: `pre-*` / `post-*` / `stop-*` / `session-start-*` / `session-end-*` / `pre-compact-*`
- 役割を続ける: `pre-dangerous-command-block.sh`, `post-auto-format.sh`
- 既存 `~/.claude/hooks/` と衝突しないこと

### Step 4: 雛形生成（骨格）

```bash
#!/bin/bash
# <name>.sh
# <event>: <目的を1行で>
#
# 入力: stdin に JSON
# 出力: exit 0 = OK / exit 1 = warning / exit 2 = block

INPUT=$(cat)

# ---- 無限ループ防止（Stop/SubagentStop のみ）----
ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
[ "$ACTIVE" = "true" ] && exit 0

# ---- 入力抽出 ----
TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')
CWD=$(echo "$INPUT" | jq -r '.cwd // ""')

# ---- early-return: 対象外なら exit 0 ----
[ "$TOOL" != "Bash" ] && exit 0

# ---- ログディレクトリ（必要時のみ）----
LOG_DIR="$HOME/.claude/.local/hooks/log"
mkdir -p "$LOG_DIR" 2>/dev/null

# ---- 本体処理 ----
if echo "$CMD" | grep -qE '<危険パターン>'; then
  echo "[Hook] BLOCKED: <理由>" >&2
  printf '{"ts":"%s","cmd":%s}\n' "$(date -u +%FT%TZ)" "$(jq -nc --arg c "$CMD" '$c')" >> "$LOG_DIR/blocked.jsonl"
  exit 2  # ツール実行を阻止
fi

exit 0
```

### Step 5: exit code 規約（CRITICAL）

| exit | 効果 |
|------|------|
| `0` | 正常終了。続行 |
| `1` | 警告（stderr の文字列はユーザーに表示される） |
| `2` | **ブロック**（PreToolUse: ツール実行阻止 / Stop: Claude Code を再起動して継続） |

Stop / SubagentStop で `{"decision":"block","reason":"..."}` を stdout に出すと、reason が新しいユーザー指示として Claude Code に返る。

### Step 6: settings.json 登録方法を提示

ユーザーに対して以下を必ず提示（自動編集はしない、`/update-config` 推奨）:

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

ユーザー設定の場合は `~/.claude/hooks/<name>.sh` の絶対パスで登録。

### Step 7: 実行権限付与

```bash
chmod +x ~/.claude/hooks/<name>.sh
```

これは作成後に必ず実行する。

## ログ追記パターン

```bash
LOG_FILE="$HOME/.claude/.local/hooks/log/<name>.jsonl"
printf '{"ts":"%s","session":"%s","data":%s}\n' \
  "$(date -u +%FT%TZ)" \
  "$(echo "$INPUT" | jq -r '.session_id // ""')" \
  "$(jq -nc --arg x "$VALUE" '$x')" >> "$LOG_FILE"
```

複数 Hook が同時書き込みする可能性がある場合は flock を使う（macOS は flock 不在のため POSIX O_APPEND の単純 append を許容、既存 `pre-dangerous-command-block.sh` 参照）。

## Anti-Patterns

- **無限ループ防止抜け**: Stop/SubagentStop で `stop_hook_active` を見ない → Claude Code が永久ループ
- **`echo $INPUT | grep`**: マルチバイト文字で破綻する。grep はファイルか `grep -F` を使う
- **無関係ツールも処理**: `tool_name` フィルタを忘れ、全 Bash で重い処理が走る
- **stdout 汚染**: PreToolUse/PostToolUse で標準出力に書くと tool_response として扱われる場合あり → ログは stderr or ファイル
- **exit code 誤用**: 通知だけなのに exit 2 → ユーザー操作が阻止される
- **権限なし**: `chmod +x` 忘れで Hook が起動しない
- **絶対パス未使用**: settings.json で相対パス → cwd 依存で動かなくなる

## チェックリスト

- [ ] shebang `#!/bin/bash` がある
- [ ] 先頭コメントで event / 目的 / exit code 規約を明記
- [ ] `INPUT=$(cat)` で stdin 受け取り
- [ ] 対象外は早期 exit 0
- [ ] Stop 系は `stop_hook_active` を見て無限ループ防止
- [ ] exit 2 でブロックする場合は stderr に理由を出す
- [ ] ログ出力先は `~/.claude/.local/hooks/log/` 配下
- [ ] settings.json 登録例を提示した
- [ ] `chmod +x` を実行した

## 関連スキル・ルール

- `create-skill` / `create-subagent` / `create-mcp-server` — 姉妹メタスキル
- `update-config` — settings.json 編集
- 既存例:
  - `~/.claude/hooks/pre-dangerous-command-block.sh`（PreToolUse ブロック例）
  - `~/.claude/hooks/stop-workflow-check.sh`（Stop + block 例）
  - `~/.claude/hooks/post-auto-format.sh`（PostToolUse 例）
  - `~/.claude/hooks/session-start-inject.sh`（SessionStart 例）
