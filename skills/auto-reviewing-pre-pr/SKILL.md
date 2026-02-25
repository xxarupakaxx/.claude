---
name: auto-reviewing-pre-pr
description: Runs automated parallel subagent review before PR creation. Launches all specialist reviewers (arch, security, perf + context-dependent reviewers) in parallel with scale-based rounds (small 2, medium 3, large 5), keeping main context clean. Use when user says "自動レビューして", "サブエージェントでレビュー", "並列レビュー", "PR前の自動チェック", or for standard/large-scale changes. Preferred over interrogating-pre-pr for typical PR workflows.
context: current
---

# Pre-PR Auto Review（サブエージェント並列自動レビュー）

## 概要

実装完了後、PR作成前に全専門サブエージェントを並列起動して自動レビューを実施。
**規模別ラウンド**（小: 2、中: 3、大: 5）のレビュー修正サイクルを、メインコンテキストを圧迫せずに実行する。

## 研究的根拠

- **[IEEE-ISTAS 2025](https://arxiv.org/abs/2506.11022)**: LLMのみの自己反復は5回で重大な脆弱性が37.6%増加。外部フィードバック必須。
- **[FDSP](https://arxiv.org/abs/2312.00024)**: 静的解析フィードバック付き反復で脆弱性率40.2%→7.4%（82%改善）。

## 既存スキルとの使い分け

| スキル | 方式 | 適用場面 |
|--------|------|----------|
| **auto-reviewing-pre-pr**（本スキル） | サブエージェント並列自動レビュー | 通常のPR前レビュー、大規模変更 |
| **interrogating-pre-pr** | ユーザーへの質問攻め | 設計意図の確認が重要な場合、小規模変更 |

## トリガー条件

- `/auto-reviewing-pre-pr` で明示的に呼び出された場合
- 「自動レビューして」「サブエージェントでレビューして」と言われた場合

## ワークフロー

### Phase 1: 変更の把握とレビューアー選定

```bash
git diff $BASE_BRANCH --stat
git diff $BASE_BRANCH --name-only
```

1. 変更ファイル・行数を把握
2. 変更内容に基づきレビューアーを選定（`@context/workflow-rules.md`のレビューアー選択ガイド参照）:
   - **常時起動**: `arch-reviewer`, `security-reviewer`, `perf-reviewer`
   - **変更内容に応じて追加**: Tier 2, Tier 3から該当するレビューアーを全て選定

### Phase 1.5: 過去の類似指摘を取得

`learnings-researcher`エージェントで、変更対象の技術領域・コンポーネントに関連する過去の知見を検索:
- solutions/から類似の問題・解決策
- issues/から既知の問題パターン

結果を**Round 1のレビューアーへのプロンプトに含める**ことで、過去に指摘された問題の再発を早期検出。
該当なしの場合はスキップ。

### Phase 2: 規模別ラウンド並列レビュー

**規模別ラウンド数**（変更ファイル数で判定）:

| 規模 | ファイル数 | 最低ラウンド |
|------|-----------|------------|
| 小 | 1-3 | 2 |
| 中 | 4-9 | 3 |
| 大 | 10+ | 5 |

各ラウンドでTaskツールにより専門サブエージェントを並列起動する。

#### Round 1: 初回全面レビュー

Taskツールで**全選定レビューアーを並列起動**:

```
各サブエージェントへのプロンプト:
- 変更対象ファイルのフルパス一覧
- git diffの内容（または差分ファイルのパス）
- レビュー観点（各レビューアー固有の観点）
- 「critical/must-fix/should-fix/minor/nit の重要度を付けて報告」
```

結果を05_log.mdに全件記録。

#### Round 2: 指摘修正 + 再レビュー（全レビューアー再起動）

1. Round 1のcritical/must-fix指摘を全て修正
2. should-fix指摘のうち正しさ・一貫性に関わるものを修正
3. **全レビューアーを再起動**し、修正が新たな問題を生んでいないか確認

**小規模の場合**: 指摘が0件（またはnit/minorのみ）なら完了。

#### Round 3以降（中・大規模時）

1. 前ラウンドの指摘を修正
2. **修正が新たな脆弱性を生んでいないか**に重点を置き、`security-reviewer`を必ず再起動
3. 他のレビューアーは指摘が残っている観点のみ再起動

**中規模 Round 3 / 大規模 Round 5**: ユーザー確認ポイント（AskUserQuestionで中間報告）

全レビューアーからの指摘が0件（またはnit/minorのみ）になるまで:
- 指摘を修正 → 再レビュー（追加ラウンド）
- **最終ラウンドで指摘が残る場合**: 合格するまで継続

### Phase 3: 最終報告 + ユーザー承認

```markdown
## Pre-PR Auto Review 結果

### ラウンド実績
- 実施ラウンド数: N（規模別: 小2/中3/大5）
- 起動レビューアー: [一覧]
- 初回検出: X件 → 最終残存: Y件（nit/minorのみ）

### ラウンドごとの推移
| Round | 検出 | 修正 | 新規 | 残存 |
|-------|------|------|------|------|
| 1     |      |      | -    |      |
| 2     |      |      |      |      |
| ...   |      |      |      |      |

### 最終レビュー結果（観点別）
- arch-reviewer: PASS / FAIL（残存指摘数）
- security-reviewer: PASS / FAIL
- perf-reviewer: PASS / FAIL
- [その他のレビューアー]: PASS / FAIL

### スキップしたnit/minor（ユーザー判断用）
- [一覧: スキップした軽微な指摘]

### 判定
全レビューアーPASS → PR作成可能
```

AskUserQuestionで最終承認を取得。

### Phase 4: PR作成へ

承認後、ユーザーの指示に従い:
- `/pr` でPR作成
- または手動でPR作成

## サブエージェントプロンプトテンプレート

各レビューアーに渡すプロンプトの共通構造:

```
あなたは{reviewer_type}として、以下の変更をレビューしてください。

## 変更対象ファイル
{file_paths}

## 変更内容（diff）
{diff_content}

## レビュー観点
{review_perspective}

## 出力形式
各指摘に以下の重要度を付けてください:
- **critical**: セキュリティ脆弱性、データ損失、本番障害に直結
- **must-fix**: バグ、仕様違反、テスト不足
- **should-fix**: 一貫性の欠如、ハードコード、不適切なエラーハンドリング
- **minor**: 命名改善、コメント追加、軽微なリファクタリング
- **nit**: スタイル、好み

## 出力フォーマット（IMPORTANT）
### [重要度] 指摘タイトル
- ファイル: path/to/file.ts:L行番号
- 問題: 具体的な問題の説明
- 修正案: **実装レベルで具体的に記述**（「〇〇のチェックを追加」ではなく「XX行の前に `if (!entity.fieldIds.includes(paramId))` を追加」のように）
- 影響: ユーザー判断に委ねる場合でも、修正しない場合の具体的リスクと技術的修正案を必ず提示
```

### security-reviewer向け追加観点（CRITICAL）

security-reviewerへのプロンプトには、以下の観点を**必ず**含めること:

```
## セキュリティ追加チェックリスト（IDOR/パラメータレベル認可）

APIエンドポイントの全リクエストパラメータ（path params, body params, query params）について:
1. **データスコープ検証**: ユーザーが指定したリソースIDが、認証済みユーザーがアクセス可能なリソースのスコープ内か？
   - 例: questionIdがattemptのquestionIdsに含まれるか、itemIdがorderのitemIdsに含まれるか
   - 認証チェック（誰がアクセス）だけでなく、認可チェック（何にアクセスできるか）まで確認
2. **マイグレーション遡及影響**: NULL許容カラム追加時、アプリコードのデフォルト値/フォールバック変更と組み合わせて既存データの振る舞いが変わらないか？
   - 例: passing_score NULLカラム追加 + DEFAULT_PASSING_SCORE変更 → 既存レコードの合格ラインが遡及変更

関連するドメインエンティティの定義（フィールド一覧）も確認し、欠落している検証を特定すること。
```

### コンテキスト拡張ルール

API routeファイルのレビュー時は、diffだけでなく以下も含めること:
- **呼び出し先のusecase/repository**: パラメータがどう使われるか追跡
- **関連するドメインエンティティ定義**: どのフィールドが検証に使えるか確認
- **マイグレーションファイル**: スキーマ変更とアプリコードのデフォルト値の整合性

## LLM連続反復ガード

**IMPORTANT**: LLMのみの修正が3回連続した場合、次のラウンドで必ず:
1. 静的解析（lint/typecheck/test）を実行
2. 全レビューアーを再起動
3. 結果をユーザーに報告

## 禁止事項

- 規模別最低ラウンド未満で完了とすること（小: 2、中: 3、大: 5）
- レビューアーの指摘をメインコンテキストで「自己判断」してスキップすること（必ず修正 or ユーザー判断）
- critical/must-fix指摘を残したままPR作成を許可すること
- LLMのみの修正を4回以上連続で行うこと
- 05_log.mdにレビュー結果を記録せずに次ラウンドに進むこと
