# メモリファイル形式

## .local/ 全体構成

```
.local/                          # MEMORY_DIR（PJ CLAUDE.mdで定義、デフォルト: .local/）
├── memory/                      # タスクごとの詳細ログ
│   ├── YYMMDD_auth-feature/     # YYMMDDは実際の日付（例: 260112 = 2026/01/12）
│   │   ├── 05_log.md
│   │   └── ...
│   └── YYMMDD_bug-fix-123/
├── memories/                    # インデックス層（検索用）
│   └── <category>/
│       └── <topic>.md
├── solutions/                   # 構造化ソリューションDB（compounding-knowledgeで生成）
│   ├── performance-issues/
│   ├── security-issues/
│   ├── runtime-errors/
│   ├── build-issues/
│   ├── architecture-decisions/
│   ├── database-issues/
│   └── integration-issues/
└── issues/                      # codebase-reviewで生成されるissueファイル
    ├── critical-sec-ユーザー入力のSQLインジェクション脆弱性.md
    ├── major-perf-ページ一覧取得でN+1クエリが発生.md
    └── ...
```

## 2層構造

| 層 | 場所 | 用途 |
|----|------|------|
| 詳細ログ | `memory/YYMMDD_<task>/` | タスクの全記録（生ログ） |
| インデックス | `memories/<category>/` | 要約・検索用（relatedで詳細を参照） |
| ソリューション | `solutions/<category>/` | 構造化された解決策DB（再利用可能） |

**検索フロー:**
1. `rg "^summary:" .local/memories/` でサマリー検索
2. 該当するメモリの`related`から詳細ログを参照

## メモリディレクトリ構成

場所: `${MEMORY_DIR}/memory/YYMMDD_<task_name>/`
- MEMORY_DIRはPJ CLAUDE.mdで定義（デフォルト: `.local/`）
- **YYMMDD**: システムプロンプトの`Today's date`から取得した実際の日付（年2桁+月2桁+日2桁）
- task_nameはタスクを識別する短い名前（例: `auth-feature`, `bug-fix-123`）
- **IMPORTANT**: 例示の日付をコピーせず、必ずシステムプロンプトの日付を使用すること

| ファイル | 用途 | 作成タイミング |
|---------|------|--------------|
| 00_spec.md | 機能要求・要件定義 | タスク開始時 |
| 05_log.md | ユーザー指示とレスポンス・実施内容のログ | タスク開始時（随時追記） |
| 10_task.md | タスク一覧 | 要件定義後 |
| 20_survey.md | 調査結果 | 調査完了後 |
| 30_plan.md | 実装計画 | 計画立案後 |
| 40_progress.md | 実装進捗 | 実装中（随時更新） |
| 80_review.md | レビュー結果 | レビュー実施後 |
| 90_pr.md | PR内容 | PR作成時 |
| 99_history.md | 意思決定ログ | 随時 |

## 05_log.md（重要）

ユーザーからの指示とそれに対するレスポンス・実施内容を逐一記録:

```markdown
# 作業ログ

## YYYY-MM-DD HH:MM - 初期指示

**ユーザー指示:**
> [最初の作業指示をここに記載]

**レスポンス:**
- [実施したこと1]
- [実施したこと2]

---

## YYYY-MM-DD HH:MM - 追加指示

**ユーザー指示:**
> [追加の指示]

**レスポンス:**
- [実施したこと]

---
```

**agent review呼び出し時**: このファイルのフルパスを明示し、agentに中身を読ませる

## 00_spec.md

```markdown
# 機能要求

## 概要
[1-2文で記述]

## 背景・目的
[なぜ必要か]

## 機能要件
### 必須要件
- [ ] 要件1

### 任意要件
- [ ] 要件1

## 非機能要件
- パフォーマンス:
- セキュリティ:

## 制約事項
- 制約1
```

## 30_plan.md

```markdown
# 実装計画

## 概要
[アプローチの概要]

## タスク一覧

### Task 1: <タスク名>
**変更対象:** <パス>

#### 1. 調査
- [ ] 項目

#### 2. 計画
- [ ] 手順

#### 3. 実行
- [ ] 実装
- [ ] コミット: `<メッセージ>`

#### 4. レビュー
- [ ] 確認項目

## agent reviewの結果
[agentからの指摘と対応]

## リスク・懸念事項
| リスク | 影響度 | 対策 |
|-------|-------|------|
```

## 40_progress.md

```markdown
# 実装進捗

## ステータス
- 開始: YYYY-MM-DD HH:MM
- 最終更新: YYYY-MM-DD HH:MM
- 進捗: XX%

## 完了タスク
- [x] タスク1 - 完了日時

## 進行中タスク
- [ ] タスク2 - 状況

## 未着手タスク
- [ ] タスク3

## 発生した問題
### 問題1
- 発生: YYYY-MM-DD
- 状況:
- 対応:
- 結果:
```

## memories/（インデックス層）

場所: `${MEMORY_DIR}/memories/<category>/<topic>.md`

タスク完了時に価値ある知見をインデックス化。要点のみ記載し、詳細はrelatedで参照。

### フォーマット

**Required:**
```yaml
---
summary: "1-2行の説明（検索の判断材料）"
created: 2026-01-14
---
```

**Optional:**
```yaml
---
summary: "N+1クエリ問題の解決 - eagerロードの適用"
created: 2026-01-14
updated: 2026-01-20
status: resolved  # in-progress | resolved | blocked | abandoned
tags: [performance, database]
related:          # 詳細ログへの参照
  - .local/memory/260114_n-plus-one-fix/
---
```

### テンプレート

```markdown
---
summary: "簡潔な説明"
created: 2026-01-14
tags: [tag1, tag2]
related:
  - .local/memory/YYMMDD_task-name/
---

# タイトル

## 要点
- ポイント1
- ポイント2

## 詳細
→ related参照
```

### 検索方法

```bash
# サマリー一覧
rg "^summary:" .local/memories/ --no-ignore --hidden

# キーワード検索
rg "^summary:.*keyword" .local/memories/ --no-ignore --hidden -i

# タグ検索
rg "^tags:.*keyword" .local/memories/ --no-ignore --hidden -i
```

## solutions/（構造化ソリューションDB）

場所: `${MEMORY_DIR}/solutions/<category>/<filename>.md`

`compounding-knowledge`スキルで生成。memories/より詳細な、再利用可能なソリューションドキュメント。
`learnings-researcher`エージェントがYAML frontmatterの各フィールドをgrep検索可能。

### カテゴリ

| カテゴリ | 内容 |
|---------|------|
| `performance-issues/` | パフォーマンス問題と最適化 |
| `security-issues/` | セキュリティ脆弱性と対策 |
| `runtime-errors/` | 実行時エラーの解決 |
| `build-issues/` | ビルド・設定・環境の問題 |
| `architecture-decisions/` | アーキテクチャ決定と根拠 |
| `database-issues/` | DB関連の問題と解決 |
| `integration-issues/` | 外部サービス連携の問題 |

新カテゴリの追加も可。

### フォーマット

```yaml
---
title: "N+1クエリによるAPI応答遅延の解決"
problem_type: "performance"    # bug|performance|security|architecture|integration|build|database
component: "users-api"
tags: [database, n-plus-one, eager-loading]
root_cause: "User.allの後にposts.countを個別クエリしていた"
solution_summary: "includes(:posts)でeager loadingを適用"
created: 2026-01-14
severity: "major"              # critical|major|minor
effort: "small"                # small|medium|large
---

# N+1クエリによるAPI応答遅延の解決

## 問題

[問題の詳細な説明]

### 症状
- 具体的な症状

### 根本原因
[root_causeの詳細]

## 解決策

### 手順
1. ステップ

### コード変更
[主要変更のハイライト]

## 予防策
- 予防策

## 参考情報
- [URL等]
```

### 検索方法

```bash
# タイトル検索
rg "^title:.*keyword" .local/solutions/ --no-ignore --hidden -i

# タグ検索
rg "^tags:.*keyword" .local/solutions/ --no-ignore --hidden -i

# root_cause検索
rg "^root_cause:.*keyword" .local/solutions/ --no-ignore --hidden -i

# コンポーネント検索
rg "^component:.*keyword" .local/solutions/ --no-ignore --hidden -i

# problem_type検索
rg "^problem_type:.*keyword" .local/solutions/ --no-ignore --hidden -i
```

**全文横断検索**: `learnings-researcher`エージェントが複数フィールドを並列grepしスコアリング。
