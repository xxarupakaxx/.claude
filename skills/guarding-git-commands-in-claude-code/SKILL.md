---
name: guarding-git-commands-in-claude-code
description: Claude Code の PreToolUse hook で、git push、reset --hard、clean、branch -D、checkout/restore . などの危険な git 操作を遮断したいときに使う。Codex の hook は設定しない。
---

# Claude Code で Git コマンドを保護する

同梱の [scripts/block-dangerous-git.sh](scripts/block-dangerous-git.sh) を Claude Code の `PreToolUse` hook として設定する。遮断対象は次のコマンドである。

- `git push`（`--force` を含む全形）
- `git reset --hard`
- `git clean -f` / `git clean -fd`
- `git branch -D`
- `git checkout .` / `git restore .`

## 設定手順

1. 適用範囲をユーザーへ尋ねる。プロジェクトだけなら `.claude/settings.json`、全プロジェクトなら `~/.claude/settings.json`。
2. スクリプトを `.claude/hooks/block-dangerous-git.sh` または `~/.claude/hooks/block-dangerous-git.sh` へコピーし、`chmod +x` を実行する。
3. 対応する settings の既存設定を保ったまま `hooks.PreToolUse` に次をマージする。

プロジェクト:

```json
{
  "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous-git.sh"}]}]}
}
```

グローバル:

```json
{
  "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "~/.claude/hooks/block-dangerous-git.sh"}]}]}
}
```

4. 遮断パターンを追加・削除するか尋ね、希望がある場合だけコピー後のスクリプトを編集する。

## 検証

```bash
echo '{"tool_input":{"command":"git push origin main"}}' | <path-to-script>
```

終了コード `2` と標準エラーの `BLOCKED` メッセージを確認する。設定を上書きせず、Claude Code の `PreToolUse` 用途だけに留める。
