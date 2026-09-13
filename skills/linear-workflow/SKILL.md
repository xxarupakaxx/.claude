---
name: linear-workflow
description: Linear MCP（mcp__claude_ai_Linear__*）で、Issue/PR/Cycle の作成・更新・検索・コメント・ステータス確認や diff 確認を依頼されたときに使う。
---

# Linear ワークフロー

Linear MCP（`mcp__claude_ai_Linear__*`）を使い、対象 ID と現在状態を確認してから Issue、Cycle、PR を扱う。MCP が未接続なら `/mcp` を案内する。Issue 作成・更新・コメントなどの外部 write は、ユーザーの明示依頼の範囲だけで行う。

## ID を確定する

依頼に必要なものだけを取得する。

| 目的 | tool |
| --- | --- |
| team | `list_teams` |
| project | `list_projects` |
| cycle | `list_cycles` |
| state | `list_issue_statuses` |
| label | `list_issue_labels` |
| assignee | `list_users` |

`team_id`、`state_id`、`assignee_id` などを名前や推測で渡さない。team が複数なら AskUserQuestion で対象を確定する。

## Issue

作成は `mcp__claude_ai_Linear__save_issue` を使う。`title` は短く明確に（70字以内を目安）、`description` は実改行の Markdown で背景・要件・Acceptance Criteria を書く。必要に応じて `team_id`、`state_id`、`assignee_id`、`cycle_id`、`project_id`、`label_ids`、`priority`（0=No、1=Urgent、2=High、3=Medium、4=Low）、`estimate` を指定する。

更新も `save_issue` に `id` を付ける。状態だけなら `id` + `state_id`、担当者だけなら `id` + `assignee_id` とし、現在状態は `get_issue` または `get_issue_status` で確認する。

検索は `mcp__claude_ai_Linear__list_issues` の team/project/cycle/assignee/state、キーワード、label、作成日範囲を必要な組み合わせで使う。「自分の issue」は `list_users` で本人の ID を確定してから絞る。作成前に類似タイトルを検索して重複を避ける。

## コメント、文書、差分

| 目的 | tool |
| --- | --- |
| コメント追加 / 取得 | `save_comment` / `list_comments` |
| 文書取得 / 保存 | `get_document` / `save_document` |
| diff 一覧 / 詳細 / thread | `list_diffs` / `get_diff` / `get_diff_threads` |

依頼された対象の ID と現在内容を先に確認し、スコープ外の修正を加えない。既存ラベルで足りない場合だけ `create_issue_label` をチームと相談して使う。

## 実行前チェック

- team、state、parent 相当の project/cycle、assignee が意図どおりか。
- state は名前文字列でなく ID か。明示されない限り作成時に `In Progress` へ進めない。
- 1 Issue に独立した複数タスクを詰め込んでいないか。
- description に API key、token、個人情報や `\n` リテラルを入れていないか。
- 大量更新、移動、ラベル作成の範囲が依頼に含まれるか。

Cycle を自動切替しない。MCP の利用可能 tool、権限、レート制限は環境に依存するため、失敗時は実行済みと未実行を分けて報告する。ラベル色は Linear UI 側で設定する。
