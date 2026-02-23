---
name: auto-reviewing-pre-pr
description: Runs automated parallel subagent review before PR creation. Launches all specialist reviewers (arch, security, perf + context-dependent reviewers) in parallel across minimum 5 rounds, keeping main context clean. Use when user says "自動レビューして", "サブエージェントでレビュー", "並列レビュー", "PR前の自動チェック", or for standard/large-scale changes. Preferred over interrogating-pre-pr for typical PR workflows.
context: current
---

# Pre-PR Auto Review（サブエージェント並列自動レビュー）

## 概要

実装完了後、PR作成前に全専門サブエージェントを並列起動して自動レビューを実施。
**最低5ラウンド**のレビュー修正サイクルを、メインコンテキストを圧迫せずに実行する。

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

### Phase 2: 5ラウンド並列レビュー

**CRITICAL**: 最低5ラウンドを実施。各ラウンドでTaskツールにより専門サブエージェントを並列起動する。

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

#### Round 2: 指摘修正 + 再レビュー

1. Round 1のcritical/must-fix指摘を全て修正
2. should-fix指摘のうち正しさ・一貫性に関わるものを修正
3. **修正箇所のみ**を対象に、関連するレビューアーを再起動

#### Round 3: 中間検証（全レビューアー再起動）

**IMPORTANT**: 修正が新たな問題を生んでいないか確認するため、全レビューアーを再起動。
- 変更全体（元の変更 + Round 1-2の修正）を対象
- 新規検出された問題を修正

**ユーザー確認ポイント**: AskUserQuestionで中間報告。

```
## Round 3 中間報告
- 初回検出: X件 → 修正済み: Y件 → 新規検出: Z件
- 残存critical/must-fix: N件
```

ユーザーに「続行」「方針変更」「中止」を確認。

#### Round 4: 修正起因の問題に焦点

1. Round 3の指摘を修正
2. **修正が新たな脆弱性を生んでいないか**に重点を置き、`security-reviewer`を必ず再起動
3. 他のレビューアーは指摘が残っている観点のみ再起動

#### Round 5: 最終検証（全レビューアー再起動）

**CRITICAL**: 全レビューアーを最終起動。変更全体を再レビュー。

全レビューアーからの指摘が0件（またはnit/minorのみ）になるまで:
- 指摘を修正 → 再レビュー（追加ラウンド）
- **Round 5以降で指摘が残る場合**: 合格するまで継続

### Phase 3: 最終報告 + ユーザー承認

```markdown
## Pre-PR Auto Review 結果

### ラウンド実績
- 実施ラウンド数: N（最低5）
- 起動レビューアー: [一覧]
- 初回検出: X件 → 最終残存: Y件（nit/minorのみ）

### ラウンドごとの推移
| Round | 検出 | 修正 | 新規 | 残存 |
|-------|------|------|------|------|
| 1     |      |      | -    |      |
| 2     |      |      |      |      |
| 3     |      |      |      |      |
| 4     |      |      |      |      |
| 5     |      |      |      |      |

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

## 出力フォーマット
### [重要度] 指摘タイトル
- ファイル: path/to/file.ts:L行番号
- 問題: 具体的な問題の説明
- 修正案: 具体的な修正方法
```

## LLM連続反復ガード

**IMPORTANT**: LLMのみの修正が3回連続した場合、次のラウンドで必ず:
1. 静的解析（lint/typecheck/test）を実行
2. 全レビューアーを再起動
3. 結果をユーザーに報告

## 禁止事項

- 5ラウンド未満で完了とすること
- レビューアーの指摘をメインコンテキストで「自己判断」してスキップすること（必ず修正 or ユーザー判断）
- critical/must-fix指摘を残したままPR作成を許可すること
- LLMのみの修正を4回以上連続で行うこと
- 05_log.mdにレビュー結果を記録せずに次ラウンドに進むこと
