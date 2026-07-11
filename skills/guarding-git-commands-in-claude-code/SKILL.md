---
name: guarding-git-commands-in-claude-code
description: 危険な git コマンド（push、reset --hard、clean、branch -D など）が実行される前に遮断する Claude Code hook を設定する。ユーザーが破壊的な git 操作の防止、git の安全 hook の追加、Claude Code での git push や reset の遮断を望む場合に使用する。
---

# Claude Code で Git コマンドを保護する

このスキルは Claude Code の `PreToolUse` hook 専用であり、Codex の hook は設定しない。

Claude が危険な git コマンドを実行する前に検知して遮断する PreToolUse hook を設定する。

## 遮断するコマンド

- `git push`（`--force` を含むすべての形）
- `git reset --hard`
- `git clean -f` / `git clean -fd`
- `git branch -D`
- `git checkout .` / `git restore .`

遮断されると、これらのコマンドへアクセスする権限がないことを伝えるメッセージが Claude に表示される。

## 手順

### 1. 適用範囲を尋ねる

**このプロジェクトだけ**（`.claude/settings.json`）にインストールするか、**すべてのプロジェクト**（`~/.claude/settings.json`）にインストールするかをユーザーに尋ねる。

### 2. hook スクリプトをコピーする

同梱スクリプトは [scripts/block-dangerous-git.sh](scripts/block-dangerous-git.sh) にある。

適用範囲に応じて、対象の場所へコピーする。

- **プロジェクト**：`.claude/hooks/block-dangerous-git.sh`
- **グローバル**：`~/.claude/hooks/block-dangerous-git.sh`

`chmod +x` で実行可能にする。

### 3. settings に hook を追加する

該当する settings ファイルへ追加する。

**プロジェクト**（`.claude/settings.json`）：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous-git.sh"
          }
        ]
      }
    ]
  }
}
```

**グローバル**（`~/.claude/settings.json`）：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block-dangerous-git.sh"
          }
        ]
      }
    ]
  }
}
```

settings ファイルがすでに存在する場合は、ほかの設定を上書きせず、既存の `hooks.PreToolUse` 配列へ hook をマージする。

### 4. カスタマイズについて尋ねる

遮断リストへパターンを追加または削除したいかをユーザーに尋ねる。
要望に応じて、コピーしたスクリプトを編集する。

### 5. 検証する

簡単なテストを実行する。

```bash
echo '{"tool_input":{"command":"git push origin main"}}' | <path-to-script>
```

終了コード 2 で終了し、標準エラー出力に BLOCKED メッセージが表示される必要がある。
