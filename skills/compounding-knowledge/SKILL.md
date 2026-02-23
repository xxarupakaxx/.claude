---
name: compounding-knowledge
description: |
  解決済み問題・知見を構造化ドキュメントとして自動キャプチャし、
  solutions/に保存するCompound Engineeringスキル。
  タスク完了後（Phase 5後）に使用。
  「知見を保存して」「解決策を記録して」「compoundして」等の依頼に対応。
  memories/のインデックスより詳細な、再利用可能なソリューションドキュメントを生成。
---

# Compounding Knowledge

解決済み問題を構造化ドキュメントとして保存し、将来の開発を加速させる。

## トリガー

### 自動トリガー（プロアクティブに実行を提案）
- **Phase 5.5**: `@context/workflow-rules.md` Phase 5.5の条件を満たす場合
- **デバッグ成功時**: エラーを調査・解決した後（「直った」「解決した」「原因がわかった」等）
- **ADR作成後**: `creating-adr`スキルでアーキテクチャ決定を記録した場合（ADRの内容をsolutions/architecture-decisions/にも変換）
- **レビューで再発パターン検出時**: auto-reviewing-pre-prで過去と同じ指摘が繰り返された場合

### 手動トリガー
- ユーザーが明示的に実行（`/compounding-knowledge`）
- 「知見を保存して」「解決策を記録して」「compoundして」等の発言

## 実行フロー

### Step 1: 情報収集

05_log.mdと関連ファイルを読み取り、以下を特定:
- 何が問題だったか
- どう解決したか
- なぜその解決策を選んだか

### Step 2: 並列サブエージェント起動

以下の4つのサブエージェント（`general-purpose`）を**並列**で起動:

#### 2-1: Solution Extractor
```
05_log.mdとdiffを分析し、以下を抽出:
- root_cause: 根本原因（1-2文）
- solution: 実際に適用した解決策の具体的手順
- code_changes: 主要なコード変更のサマリー
```

#### 2-2: Prevention Strategist
```
この問題の再発を防ぐための戦略を提案:
- prevention: 予防策のリスト
- detection: 早期発見方法
- related_patterns: 類似問題のパターン
```

#### 2-3: Category Classifier
```
solutions/の既存カテゴリを確認し、最適なカテゴリとファイル名を決定:
- category: solutions/下のサブディレクトリ名
- filename: kebab-caseのファイル名（.md）
既存カテゴリ: performance-issues, security-issues, runtime-errors,
build-issues, architecture-decisions, database-issues, integration-issues
新カテゴリの作成も可。
```

#### 2-4: Related Docs Finder
```
関連する外部ドキュメント・GitHub Issue・Stack Overflowの記事を検索:
- references: 関連URLのリスト
- related_solutions: solutions/内の関連ドキュメント
```

### Step 3: ドキュメント生成

サブエージェントの結果を統合し、以下の形式でドキュメントを生成:

```markdown
---
title: "問題のタイトル"
problem_type: "bug|performance|security|architecture|integration|build|database"
component: "影響を受けたコンポーネント"
tags: [tag1, tag2, tag3]
root_cause: "根本原因の1行サマリー"
solution_summary: "解決策の1行サマリー"
created: YYYY-MM-DD
severity: "critical|major|minor"
effort: "small|medium|large"
---

# [タイトル]

## 問題

[問題の詳細な説明]

### 症状
- 具体的な症状1
- 具体的な症状2

### 根本原因
[root_causeの詳細説明]

## 解決策

### 手順
1. ステップ1
2. ステップ2

### コード変更
[主要な変更のハイライト]

## 予防策

- 予防策1
- 予防策2

## 参考情報

- [関連URL1]
- [関連URL2]
- 関連ソリューション: [solutions/内のパス]
```

### Step 4: 保存 & インデックス更新

1. `${MEMORY_DIR}/solutions/<category>/<filename>.md` に保存
2. 必要に応じて `memories/` にもインデックスを作成/更新
3. 保存完了をユーザーに報告

## solutions/ ディレクトリ構造

```
${MEMORY_DIR}/
├── solutions/                    # 構造化ソリューションDB
│   ├── performance-issues/
│   ├── security-issues/
│   ├── runtime-errors/
│   ├── build-issues/
│   ├── architecture-decisions/
│   ├── database-issues/
│   └── integration-issues/
├── memories/                     # インデックス層（既存）
└── memory/                       # タスクログ（既存）
```

## 検索との連携

保存されたソリューションは `learnings-researcher` エージェントが検索可能。
YAML frontmatterの各フィールド（title, tags, root_cause, component, problem_type）が
grep対象となるため、フィールドは正確に記入すること。
