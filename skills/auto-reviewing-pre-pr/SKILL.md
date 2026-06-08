---
name: auto-reviewing-pre-pr
description: Runs automated parallel subagent review before PR creation. Launches all specialist reviewers (arch, security, perf + context-dependent reviewers) in parallel with scale-based rounds (small 1, medium 2, large 3), keeping main context clean. Use when user says "自動レビューして", "サブエージェントでレビュー", "並列レビュー", "PR前の自動チェック", or for standard/large-scale changes. Preferred over interrogating-pre-pr for typical PR workflows.
context: current
---

# Pre-PR Auto Review（サブエージェント並列自動レビュー）

## 概要

実装完了後、PR作成前に全専門サブエージェントを並列起動して自動レビューを実施。
**規模別ラウンド**（小: 1、中: 2、大: 3）のレビュー修正サイクルを、メインコンテキストを圧迫せずに実行する。

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
| 小 | 1-3 | 1 |
| 中 | 4-9 | 2 |
| 大 | 10+ | 3 |

**注**: 指摘が残っている場合のみ追加ラウンドを実行。Round 1で指摘0件なら小規模は完了。

各ラウンドでTaskツールにより専門サブエージェントを並列起動する。

#### Round 1: 初回全面レビュー

Taskツールで**全選定レビューアーを並列起動**:

```
各サブエージェントへのプロンプト:
- 変更対象ファイルのフルパス一覧
- git diffの内容（または差分ファイルのパス）
- レビュー観点（各レビューアー固有の観点）
- 「CRITICAL/IMPORTANT/MINOR の重要度を付けて報告」
```

結果を05_log.mdに全件記録。

#### Round 2: 指摘修正 + 再レビュー（全レビューアー再起動）

1. Round 1のCRITICAL指摘を全て修正
2. IMPORTANT指摘のうち正しさ・一貫性に関わるものを修正
3. **全レビューアーを再起動**し、修正が新たな問題を生んでいないか確認

**全規模共通**: 指摘が0件（またはMINORのみ）なら完了。追加ラウンドは指摘がある場合のみ。

#### Round 3（大規模のみ、指摘がある場合）

1. 前ラウンドの指摘を修正
2. **修正が新たな脆弱性を生んでいないか**に重点を置き、`security-reviewer`を必ず再起動
3. 他のレビューアーは指摘が残っている観点のみ再起動

**大規模 Round 3**: ユーザー確認ポイント（AskUserQuestionで最終報告）

全レビューアーからの指摘が0件（またはMINORのみ）になるまで:
- 指摘を修正 → 再レビュー（追加ラウンド）
- **最終ラウンドで指摘が残る場合**: 合格するまで継続

### Phase 3: 最終報告 + ユーザー承認

```markdown
## Pre-PR Auto Review 結果

### ラウンド実績
- 実施ラウンド数: N（規模別: 小2/中3/大5）
- 起動レビューアー: [一覧]
- 初回検出: X件 → 最終残存: Y件（MINOR のみ）

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

### スキップしたMINOR（ユーザー判断用）
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
各指摘に以下の重要度を付けてください（3階級統一）:
- **CRITICAL**: セキュリティ脆弱性、データ損失、本番障害、バグ、仕様違反、テスト不足（必ず修正）
- **IMPORTANT**: 一貫性の欠如、ハードコード、不適切なエラーハンドリング（修正推奨。正しさに関わるものは必須）
- **MINOR**: 命名改善、コメント追加、軽微なリファクタリング、スタイル・好み（スキップ可）

> 旧用語マッピング（互換参考）: `critical` + `must-fix` → `CRITICAL`、`should-fix` → `IMPORTANT`、`minor` + `nit` → `MINOR`

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

## 収束判定（CRITICAL）

各ラウンド終了時に以下のいずれかを返し、無限ループを防ぐ:

| 状態 | CRITICAL | IMPORTANT | round | 同一指摘 持続 | LLM連続失敗 | 判定 | アクション |
|------|---------|----------|-------|-------------|-----------|------|----------|
| A | 0 | <3 | any | - | - | **CONVERGED** | Phase 3（最終報告）へ |
| B | 0 | ≥3 | <max | - | - | **CONTINUE** | 次ラウンド実行 |
| B' | 0 | ≥3 | ≥max（小3/中5/大8） | - | - | **ESCALATE** | 残存IMPORTANT一覧を提示し AskUserQuestion で人間判断 |
| C | ≥1 | - | <max | <3 | - | **CONTINUE** | 次ラウンド実行 |
| D | ≥1 | - | <max | ≥3 | - | **ESCALATE** | AskUserQuestion で人間判断 |
| E | ≥1 | - | ≥max（小3/中5/大8） | - | - | **ESCALATE** | 残存指摘一覧を提示し最終承認 |
| F | - | - | - | - | ≥3 | **ABORT** | LLM単独修正打ち切り、静的解析と人間確認を強制 |

> max ラウンド: 小=3 / 中=5 / 大=8（規模別ハード上限。それを超えても収束しないなら設計レベルの問題）

### Severity 閾値（運用ルール）

- **CRITICAL**: 全ラウンドで必須修正。3ラウンド連続残存で **ESCALATE**
- **IMPORTANT**: 一貫性・正しさに関わるものは Round 2 まで必須修正
- **MINOR**: スキップ可（最終レポートに記録）
- **info-needed**: 必ずユーザーに確認。Round 1 で出たら即時 AskUserQuestion

### 同一指摘の判定（issues/ frontmatter ベース）

`${MEMORY_DIR}/issues/*.md` の frontmatter から同一指摘を識別:
- `issue_id` が同じ → 同一指摘
- 連続 3 ラウンド `status: pending` → 持続中（マトリクス D 該当）

詳細は後述の「文脈伝播（issues/ frontmatter）」セクション参照。

## LLM連続反復ガード

**IMPORTANT**: LLMのみの修正が3回連続した場合、次のラウンドで必ず:
1. 静的解析（lint/typecheck/test）を実行
2. 全レビューアーを再起動
3. 結果をユーザーに報告

連続4回以上は **ABORT**（マトリクス F）。

## 文脈伝播（issues/ frontmatter）

**IMPORTANT**: ループ間で「どの reviewer が何を検出したか」を保持し、再レビュー時の優先順位付けに使う。

### issues/ ファイル frontmatter 拡張

`${MEMORY_DIR}/issues/{priority}-{reviewer}-{title}.md` の frontmatter に以下を追加:

```yaml
---
# 既存
priority: CRITICAL              # CRITICAL / IMPORTANT / MINOR
category: sec
type: bug

# 拡張（後方互換: 未指定でも動作）
issue_id: ISS-001               # checkpoint.md から参照される一意ID
detected_by: security-reviewer  # 検出した reviewer 名
first_detected_round: 1         # 初回検出のラウンド番号
status: pending                 # pending / fixed / reopened / dismissed
re_review_priority: high        # high / medium / low
---
```

### checkpoint.md 連携

各ラウンド終了時、未解決 issue を checkpoint.md に列挙:

```markdown
## 修正対象 issue
- issue_id: ISS-001
  file: issues/CRITICAL-security-reviewer-sql-injection.md
  detected_by: security-reviewer
  first_detected_round: 1
  status: pending
  re_review_priority: high
```

### 次ラウンドの reviewer 選定ロジック

- 同一 issue が `status: pending` のまま残存 → **検出元 reviewer のみ** 再起動（最小限）
- 新規 issue 検出 → 通常の規模別ラウンドに合流
- `first_detected_round` から計算した persistence が 3+ → ESCALATE 候補

### issues/ frontmatter ライフサイクル管理（運用手順）

各ラウンドでメインの Codex は以下を実行する（自動運用の主体・タイミングを明示）:

1. **ラウンド開始時**:
   - `glob` で `${MEMORY_DIR}/issues/*.md` を取得
   - `status: pending` のファイル一覧を抽出（例: `grep -l "^status: pending" "${MEMORY_DIR}/issues/"*.md`）
   - 取得した一覧を各レビューアープロンプトに渡す（重複検出のため）

2. **レビュー実行**:
   - 新規検出 issue は `issue_id` を採番（既存 ID と重複しない `ISS-NNN` 形式）
   - frontmatter に `detected_by`, `first_detected_round`, `status: pending`, `re_review_priority` を必ず記載

3. **修正後**:
   - 修正完了した issue は Edit ツールで `status: fixed` に更新
   - 該当しなくなった issue（リファクタで消失等）は `status: dismissed` に更新

4. **ラウンド終了時**:
   - 同一 `issue_id` が 3 ラウンド連続 `status: pending` → 状態 D（ESCALATE）へ遷移
   - 新規未解決 issue が `IMPORTANT≥3` → 状態 B/B' へ遷移

5. **記録**:
   - 各ラウンドの遷移状況を `${MEMORY_DIR}/memory/<task>/05_log.md` に記録（監査証跡）

## 禁止事項

- 指摘が残っているのにラウンドを打ち切ること
- レビューアーの指摘をメインコンテキストで「自己判断」してスキップすること（必ず修正 or ユーザー判断）
- CRITICAL指摘を残したままPR作成を許可すること
- LLMのみの修正を4回以上連続で行うこと
- 05_log.mdにレビュー結果を記録せずに次ラウンドに進むこと
