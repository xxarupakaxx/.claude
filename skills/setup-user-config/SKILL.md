---
name: setup-user-config
description: ユーザーが `~/.claude/config/user.json` の初期化・更新を明示したとき、`user.example.json` と既存値を照合して不足分を質問し、確認後に保存・検証する。通常の作業開始だけでは使わない。
allowed-tools: Read, Write, Bash, Glob, AskUserQuestion
---

# Setup User Config

`~/.claude/config/user.json`（Layer 2: マシン固有ユーザー設定）をインタラクティブに初期化・更新する。

## トリガー

- 新規マシンで `config/user.json` が存在しないことを確認し、ユーザーが初期化を求めた
- ユーザーが「設定を初期化」「setup」「user.json を作って」等を依頼
- `/setup-user-config` 実行時

## 前提

- テンプレート: `~/.claude/config/user.example.json`（git管理）
- 出力先: `~/.claude/config/user.json`（gitignore済み）
- 3層構成の Layer 2 に該当（参照: `context/loop-engineering.md`）

## 実行フロー

### Step 1: 現状チェック

```
Read ~/.claude/config/user.example.json → テンプレート取得
Read ~/.claude/config/user.json → 既存設定の有無を確認
```

- **新規**: user.json が存在しない → Step 2 へ（全フィールド入力）
- **更新**: user.json が存在する → Step 2 へ（現在値をデフォルトとして表示）

### Step 2: フィールド入力

`user.example.json` の現在のフィールドを読み、AskUserQuestion で不足値または変更希望の値だけを収集する。テンプレートにないフィールドを創作しない。

既存の user.json がある場合は現在値を保持し、変更対象以外を再入力させない。現在値をデフォルト選択肢に含める。

**収集フィールド（user.example.json に準拠）:**

| フィールド | 説明 | 自動検出 |
|-----------|------|---------|
| `user.email` | メールアドレス | `git config user.email` |
| `user.github_username` | GitHub ユーザー名 | `gh api user --jq .login` |
| `slack.notification_channel` | Slack通知チャンネル | — |
| `slack.dm_fallback` | DM fallback有無 | デフォルト true |
| `jira.assignee_jql` | Jira担当者JQL | デフォルト `assignee = currentUser()` |
| `jira.default_project` | Jiraデフォルトプロジェクト | — |

**自動検出ロジック:**

```bash
# email
git config user.email

# github_username
gh api user --jq .login 2>/dev/null || echo ""
```

自動検出できた値はデフォルト選択肢の先頭に `(検出)` 付きで表示。
検出できなかった場合は手入力を促す。

### Step 3: 確認 & 書き込み

1. 収集した値で JSON を組み立て、プレビューとして表示
2. AskUserQuestion で最終確認（「このまま保存」/「修正する」）
3. 承認後に Write で `~/.claude/config/user.json` に保存

### Step 4: 検証

保存後、以下を確認して結果を報告:
- JSON パース可能か（`Bash: python3 -m json.tool ~/.claude/config/user.json`）
- gitignore されているか（対象の git root から `Bash: git check-ignore ~/.claude/config/user.json`）。対象外なら `未確認` とする。

## テンプレート拡張時の対応

`user.example.json` にフィールドが追加された場合:
1. 既存 `user.json` を Read
2. テンプレートとの差分フィールドのみ AskUserQuestion で収集
3. 既存値を保持しつつ新フィールドを追加

## 関連

- `context/loop-engineering.md` — 3層構成の全体像
- `skills/project-init/` — Layer 3（プロジェクト側）の初期化
- `config/user.example.json` — テンプレート（git管理）
