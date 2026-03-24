---
name: team-builder
description: "タスクに最適なエージェントチームを対話的に構成するスキル。利用可能なエージェントを一覧・分類し、タスクに応じた最適な組み合わせを提案。agent-teamsの前段として使用。"
---

# Team Builder — エージェントチーム構成

## 概要

`~/.claude/agents/`配下の全エージェントを一覧し、タスクに最適なチームを対話的に構成する。
`agent-teams`や`orchestrate`の前段として使用。

## トリガー

- 「チームを組んで」
- 「どのエージェントを使うべき？」
- `/team-builder <タスク説明>`
- 複雑なタスクでエージェント選択に迷った時

## エージェントカタログ

### 自動スキャン

`~/.claude/agents/*.md` を全て読み取り、以下を抽出:
- 名前
- 説明（description）
- 得意分野
- 入力要件

### カテゴリ分類

| カテゴリ | エージェント |
|----------|------------|
| **設計・計画** | requirement-parser, implementation-planner, go-nogo-advisor |
| **レビュー（Tier 1）** | arch-reviewer, security-reviewer, perf-reviewer |
| **レビュー（Tier 2）** | test-reviewer, code-quality-reviewer, code-simplicity-reviewer, error-handling-reviewer, observability-reviewer |
| **レビュー（Tier 3）** | i18n-reviewer, compliance-reviewer, devops-reviewer, rule-validator |
| **UI/UX** | a11y-reviewer, ui-ux-reviewer |
| **API** | api-designer, api-contract-reviewer |
| **探索・分析** | architecture-explorer, data-flow-tracer, dependency-mapper |
| **データ** | data-modeler |
| **リファクタリング** | refactoring-advisor |
| **評価** | technical-evaluator |
| **ドキュメント** | docs-reviewer, prd-reviewer |
| **並行処理** | concurrency-reviewer |

## チーム構成プロセス

### Step 1: タスク分析

タスク説明から以下を判定:
- 変更の種類（新機能/修正/リファクタ/セキュリティ）
- 変更対象の技術領域（API/UI/DB/インフラ）
- 変更規模（小/中/大）

### Step 2: 自動推薦

`workflow-rules.md`のレビューアー選択ガイドに基づき推薦:

```markdown
## 推薦チーム

### 必須（Tier 1）
- arch-reviewer: アーキテクチャ検証
- security-reviewer: セキュリティ検証
- perf-reviewer: パフォーマンス検証

### 推薦（Tier 2）
- test-reviewer: テスト変更あり
- api-contract-reviewer: API変更あり

### オプション
- compliance-reviewer: 個人情報取扱あり
```

### Step 3: ユーザー確認

AskUserQuestionで:
- 推薦チームの承認/修正
- 追加エージェントの選択
- 不要エージェントの除外

### Step 4: チーム出力

承認されたチームを以下の形式で出力:

```markdown
## Team Composition
- agents: [arch-reviewer, security-reviewer, perf-reviewer, test-reviewer]
- model: sonnet (レビュー用)
- parallel: true
- rounds: 2 (中規模)
```

この出力を`/orchestrate`や`auto-reviewing-pre-pr`に渡して実行。
