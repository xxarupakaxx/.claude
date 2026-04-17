---
name: compounding-knowledge
description: |
  解決済み問題・知見を構造化ドキュメントとして自動キャプチャし、
  solutions/に保存するCompound Engineeringスキル。
  タスク完了後（Phase 5後）に使用。
  「知見を保存して」「解決策を記録して」「compoundして」等の依頼に対応。
  memories/のインデックスより詳細な、再利用可能なソリューションドキュメントを生成。
  **技術調査で得た知見（SDK API発見、ライブラリ挙動、設計パターン等）も
  solutions/technical-learnings/ に保存する。**
---

# Compounding Knowledge

解決済み問題**および技術調査で得た知見**を構造化ドキュメントとして保存し、将来の開発を加速させる。

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

### Step 1: 情報収集 & 知見タイプ判別

05_log.mdと関連ファイルを読み取り、以下の**2種類の知見**を特定:

#### タイプA: Solution（問題解決パターン）
- 何が問題だったか → どう解決したか → なぜその解決策を選んだか
- 保存先: `solutions/<category>/`

#### タイプB: Technical Learning（技術調査知見）
- Phase 1-2でSDK/ライブラリ/APIを調査して得た発見
- 計画・実装に影響を与えた技術的な知見
- 例: 「AI SDK onStepFinishでツール呼び出しをフックできる」「AsyncLocalStorageでリクエストスコープを伝播できる」
- 保存先: `solutions/technical-learnings/`

**判別基準**: 「問題→原因→修正」の流れがあるか（→Solution）、「調査→発見→活用」の流れか（→Technical Learning）。1つのセッションで両方存在することが多い。

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

サブエージェントの結果を統合し、知見タイプに応じたテンプレートでドキュメントを生成:

#### タイプA: Solution テンプレート

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

### 根本原因
[root_causeの詳細説明]

## 解決策

### 手順
1. ステップ1

### コード変更
[主要な変更のハイライト]

## 予防策
- 予防策1

## 参考情報
- 関連ソリューション: [solutions/内のパス]
```

#### タイプB: Technical Learning テンプレート

```markdown
---
title: "発見・知見のタイトル"
learning_type: "api-discovery|library-behavior|design-pattern|integration-technique|performance-insight"
source: "調査元（Context7/deepwiki/公式ドキュメント/実験等）"
component: "適用先コンポーネント"
tags: [tag1, tag2, tag3]
discovery_summary: "発見の1行サマリー"
applied_in: "この知見を適用したコミットやファイル"
created: YYYY-MM-DD
confidence: "verified|experimental|theoretical"
---

# [タイトル]

## 発見

[何を調べて何がわかったか]

### 背景・動機
- なぜこれを調べたか（どんな課題を解決しようとしていたか）

### 調査結果
[具体的な発見内容。コード例を含む]

## 活用パターン

### 適用方法
[この知見をどう実装に活かしたか]

### コード例
[実際のコードまたは最小限の例]

## 注意点・制約
- 既知の制限やエッジケース

## 参考情報
- [公式ドキュメントURL等]
```

### Step 4: 提案 & ユーザー承認（IMPORTANT）

**Edit禁止ポリシー**: knowledge管理ファイルへの直接書き込みは禁止。

1. **生成したドキュメントを提案として表示**
   ```markdown
   ## 保存提案

   **保存先**: `${MEMORY_DIR}/solutions/<category>/<filename>.md`

   ---
   [生成したドキュメント全文]
   ---
   ```

2. **AskUserQuestionで承認を取得**
   - 「このまま保存」
   - 「修正して保存」（修正点を入力）
   - 「保存しない」

3. **承認後のみWriteツールで保存**
   - 保存後、`index.json`に新規エントリを追加（ref_count: 0）

4. 必要に応じて `memories/` にもインデックスを作成（同様に提案→承認）

## solutions/ ディレクトリ構造

```
${MEMORY_DIR}/
├── solutions/                    # 構造化ソリューション & 知見DB
│   ├── performance-issues/
│   ├── security-issues/
│   ├── runtime-errors/
│   ├── build-issues/
│   ├── architecture-decisions/
│   ├── database-issues/
│   ├── integration-issues/
│   └── technical-learnings/      # 技術調査知見（API発見、ライブラリ挙動等）
├── memories/                     # インデックス層（既存）
└── memory/                       # タスクログ（既存）
```

## 検索との連携

保存されたソリューション・技術知見は `learnings-researcher` エージェントが検索可能。
YAML frontmatterの各フィールド（title, tags, root_cause/discovery_summary, component, problem_type/learning_type）が
grep対象となるため、フィールドは正確に記入すること。
