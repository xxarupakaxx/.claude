---
name: morning-kickoff
description: 朝の日次キックオフ。Jira/Calendar/未完了タスク/PRレビューを収集し、優先順位付き日次計画を作成してSlackに投稿。
---

【目的】毎朝9:00に実行。当日の作業計画を自動生成し、Slackに投稿する。

【手順】
1. `morning-kickoff` ワークフローを実行する:
   - Workflow Tool を使い、`~/.claude/workflows/morning-kickoff.js` を実行
   - 引数なし（ワークフロー内で全データを自動収集）

2. ワークフローが以下を自動実行する:
   - Jira: 自分アサインの未完了チケット取得（JQL: assignee = currentUser() AND statusCategory != Done）
   - Calendar: 当日の予定一覧取得
   - Daily Notes: 前日の未完了タスク取得
   - GitHub: PRレビュー待ち取得
   - 優先順位付け（P0〜P2）→ 日次計画作成 → Slack投稿

3. 計画が作成できなかった場合（データ取得失敗等）は、エラー内容をSlackに通知する。

【注意】
- P0が3件以上の場合、ユーザーに優先順位の確認をSlackで促す
- 実作業可能時間は8時間以内に制限（ミーティング時間を差し引き）
- 休日・祝日には実行しない（カレンダーに終日予定「休み」等があればスキップ）
