---
name: linear-workflow
description: Linear MCP（mcp__claude_ai_Linear__*）を使い、Issue/PR/Cycle 連携を自動化するスキル。Linear Issue の作成・更新・検索・ステータス変更・コメント追加・サイクル/チーム/プロジェクト確認・PR 差分確認を扱う。「Linear issue 立てて」「Linear にチケット作って」「Linear のステータス更新して」「Linear のサイクル issue 一覧」「Linear で issue 検索」「Linear に issue 検索して」「Linear issue にコメント」「Linear で PR 差分確認」「Linear の自分の issue 」等の依頼が来たら必ず使うこと。
---

# Linear ワークフロー操作スキル

Linear MCPツール（`mcp__claude_ai_Linear__*`）を使い、Issue/Cycle/PR 連携を自動化する。

## トリガー条件

以下の依頼が来たら自動適用する:
- 「Linear issue 立てて」「Linear にチケット作って」「Linear に起票」
- 「Linear のステータス更新」「ステータスを X に変えて」
- 「自分のサイクル issue 一覧」「今のサイクルの issue」
- 「Linear で issue 検索」「assignee で絞り込み」
- 「Linear issue にコメント」「Linear にコメント残して」
- 「PR 差分を確認」「Linear の diff 見せて」

## 前提

- MCPサーバー `claude.ai Linear` が接続済みであること
- 未接続の場合はユーザーに `/mcp` での再接続を案内

## ワークフロー

### Step 1. コンテキスト確認（Team / Project / Cycle）

Issue 作成・検索の前に必要なIDを必ず確認する。

| 目的 | ツール |
|---|---|
| チーム一覧（team_id 取得） | `mcp__claude_ai_Linear__list_teams` |
| プロジェクト一覧 | `mcp__claude_ai_Linear__list_projects` |
| 現在のサイクル確認 | `mcp__claude_ai_Linear__list_cycles` |
| ステータス（state）一覧 | `mcp__claude_ai_Linear__list_issue_statuses` |
| ラベル一覧 | `mcp__claude_ai_Linear__list_issue_labels` |
| ユーザー（assignee）一覧 | `mcp__claude_ai_Linear__list_users` |

**CRITICAL**: `team_id` が不明な場合は推測せず、`list_teams` で先に取得する。複数チームある場合は AskUserQuestion で対象チームを確認する。

### Step 2. Issue 作成

`mcp__claude_ai_Linear__save_issue` で作成。主要フィールド:

| フィールド | 説明 |
|---|---|
| `title` | Issue タイトル（短く明確に。70字以内目安） |
| `description` | Markdown。背景・要件・受け入れ基準を含める |
| `team_id` | Step 1 で取得 |
| `state_id` | `list_issue_statuses` で取得（例: Backlog / Todo / In Progress） |
| `assignee_id` | `list_users` で取得（自分にアサインする場合は本人） |
| `cycle_id` | 現在/次サイクル ID（任意） |
| `project_id` | プロジェクト所属する場合（任意） |
| `label_ids` | ラベル ID 配列（任意） |
| `priority` | 0=No / 1=Urgent / 2=High / 3=Medium / 4=Low |
| `estimate` | ストーリーポイント（チーム設定による） |

**改行ルール**: `description` には実改行を含める（`\n` リテラルではなく実際の改行文字）。

### Step 3. Issue 更新（ステータス変更含む）

同じ `save_issue` を `id` 付きで呼ぶことで更新になる。

- ステータスのみ変更: `id` + `state_id` を渡す
- assignee 変更: `id` + `assignee_id`
- 現在状態確認: `mcp__claude_ai_Linear__get_issue` または `get_issue_status`

### Step 4. Issue 検索

`mcp__claude_ai_Linear__list_issues` でフィルタ:
- `team_id` / `project_id` / `cycle_id` / `assignee_id` / `state_id`
- キーワード / ラベル / 作成日範囲
- 「自分の」依頼時は `list_users` で本人を特定 → `assignee_id` 指定

### Step 5. コメント / ドキュメント

| 目的 | ツール |
|---|---|
| コメント追加 | `mcp__claude_ai_Linear__save_comment` |
| コメント一覧 | `mcp__claude_ai_Linear__list_comments` |
| ドキュメント取得 | `mcp__claude_ai_Linear__get_document` |
| ドキュメント保存 | `mcp__claude_ai_Linear__save_document` |

### Step 6. PR 差分 / Diff 確認

| 目的 | ツール |
|---|---|
| Diff 一覧 | `mcp__claude_ai_Linear__list_diffs` |
| Diff 詳細 | `mcp__claude_ai_Linear__get_diff` |
| Diff スレッド | `mcp__claude_ai_Linear__get_diff_threads` |

### Step 7. ラベル運用

既存ラベルが目的に合わなければ `mcp__claude_ai_Linear__create_issue_label` で新規作成（チームと相談の上）。

## 実行前チェックリスト

1. `team_id` は確定しているか？（複数チーム所属時は AskUserQuestion）
2. `state_id` は意図したワークフローステートか？（Backlog/Todo/In Progress の取り違え注意）
3. `description` に受け入れ基準（Acceptance Criteria）を入れたか？
4. `assignee` を指定すべきタスクか、未アサインで起票すべきか？
5. サイクル/プロジェクトに紐付けるべきか？

## Anti-Patterns（禁止事項）

- `team_id` を推測で渡す（必ず `list_teams` で確認）
- `state_id` を名前文字列（"In Progress"）のまま渡す（必ず ID）
- `description` に `\n` リテラルを書く（実改行を使う）
- 検索せずに重複 Issue を作成する（先に `list_issues` で類似タイトルを確認）
- 作成と同時に状態を勝手に "In Progress" にする（明示依頼がなければ Backlog/Todo）
- 1 Issue に複数の独立タスクを詰め込む（粒度を分ける）
- 機密情報（API キー・トークン・個人情報）を description に貼る

## 既知の制限

- Linear MCP の利用可能ツールは環境により異なる。未接続の場合は `/mcp` 案内
- Cycle の自動切替は行わない（明示指定）
- ラベルカラーは Linear UI 側で設定推奨
