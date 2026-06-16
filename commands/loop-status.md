---
name: loop-status
description: Loop Engineering System の全体ステータスを表示
---

Loop Engineering System の現在の状態を一覧表示してください。

## 収集する情報

### 1. スケジュールタスク
`~/.claude/scheduled-tasks/` 配下の各タスクについて:
- タスク名
- 最終実行時刻（ログがあれば）
- ステータス（正常/エラー/未実行）

### 2. ワークフロー
`~/.claude/workflows/` 配下の各ワークフローについて:
- 名前と説明（meta.name, meta.description）
- 最近の実行履歴（あれば）

### 3. コスト状況
`~/.claude/.local/cost-track/` の本日分ログから:
- 本日のツール呼び出し回数
- アラートレベル（ok/info/warning/critical）

### 4. 改善提案
`~/.claude/.local/harness-suggestions/` の未レビュー提案:
- 件数
- 最新の提案サマリー

### 5. エージェント一覧
Loop Engineering用のエージェント（`~/.claude/agents/` 配下）:
- orchestrator, implementer, cost-monitor, minutes-classifier, jira-spec-writer, ab-judge, harness-improver, daily-planner

## 出力形式

```
=== Loop Engineering Status ===

[Scheduled Tasks]
  morning-kickoff   : last=09:00 status=ok
  hour-calnedar     : last=15:00 status=ok
  jira-spec-poll    : last=15:00 status=ok
  evening-review    : last=18:00 status=ok

[Workflows]
  tournament-ab          : available
  morning-kickoff        : available
  implementation-drive   : available
  evening-review         : available

[Cost Today]
  Tool calls: 142
  Alert: ok

[Harness Suggestions]
  Unreviewed: 2
  Latest: "繰り返しRead検出 — キャッシュ戦略を提案"

[Agents] 8 active (orchestrator, implementer, ...)
```

情報が取得できない項目は「N/A」と表示してください。
