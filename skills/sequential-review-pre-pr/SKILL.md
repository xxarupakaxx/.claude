---
name: sequential-review-pre-pr
description: 2段階レビュー。軽量Stage 1（必須3観点）で問題なければStage 2をスキップしてコスト削減。Stage 1で重大指摘が出たら全観点レビューに昇格。小〜中規模変更で auto-reviewing-pre-pr のコスト削減版として使用。「2段階レビューして」「Stage1から」等の依頼に対応。
context: current
---

# Sequential Review Pre-PR（2段階レビュー）

## 概要

実装完了後、PR 作成前に **段階的に** レビューを実施し、コストとカバレッジのバランスを取る。

- Stage 1: 必須3観点（prd / rule-validator / arch）のみ並列起動（spec compliance 先行）
- Stage 1 PASS → Phase 4 へ（コスト約 1/5）
- Stage 1 FAIL → Stage 2（全観点レビュー）に昇格

## 研究的根拠

- **WebSearch 由来の業界知見**: 2段階構成で **token cost -60〜90%**（spec違反時に quality leg 全部スキップ可能）
- **小規模変更（1-3 files / <50 LOC）**: Stage 1 のみ実行で完了する想定（CRITICAL=0 を期待）。エージェント数 1/5、auto-reviewing-pre-pr より低コスト
- **中〜大規模（4+ files）**: Stage 1 で根本問題を捕捉 → Stage 2 昇格、または直接 auto-reviewing-pre-pr を推奨
- obra/superpowers の "Only dispatch after spec compliance review passes" 原則に基づく

## auto-reviewing-pre-pr との使い分け

| スキル | 適用場面 |
|--------|----------|
| **sequential-review-pre-pr**（本スキル） | 軽微〜中規模変更、コスト優先、定型変更 |
| **auto-reviewing-pre-pr** | 大規模変更、セキュリティ・性能クリティカル領域、最初から全観点を回したい |

## トリガー条件

- `/sequential-review-pre-pr` で明示的に呼び出された場合
- 「2段階レビューして」「Stage1から」と言われた場合
- 変更が 1-3 files / <50 LOC で `auto-reviewing-pre-pr` を呼ばれた場合（推奨提示）

## ワークフロー

### Phase 1: 起動条件判定

```bash
git diff $BASE_BRANCH --stat
```

| 条件 | 動作 |
|------|------|
| 1-3 files かつ <50 LOC | Stage 1 のみ実行を提案 |
| 4-9 files | Stage 1 → 必要に応じ Stage 2 |
| 10+ files | auto-reviewing-pre-pr を推奨（本スキルでは Stage 2 必須） |

### Phase 2: Stage 1 — 軽量レビュー

Task ツールで以下を **並列起動**（spec compliance 先行）:

- `prd-reviewer` (opus, 要件・仕様との乖離検出)
- `rule-validator` (sonnet, AGENTS.md/rules/ への準拠)
- `arch-reviewer` (sonnet, アーキテクチャ整合性)

> **設計意図（obra/superpowers パターン）**: spec/rule/arch 違反があるなら、quality reviewer を全部走らせるのは無駄。Stage 1 で根本問題を潰してから Stage 2 へ進む。

各 reviewer のプロンプトに以下を追記:

> 重大な問題（CRITICAL）が見つかった場合、または「より広範な観点でのレビューが必要」と判断した場合、出力末尾に `NEEDS_DEEPER_REVIEW: true` と書いてください。

### Phase 2.5: Stage 1 評価

| 結果 | 判定 | 次アクション |
|------|------|------------|
| CRITICAL=0, IMPORTANT≤2, NEEDS_DEEPER_REVIEW=false | Stage 1 PASS | Phase 4（最終報告）へ |
| CRITICAL≥1（spec/rule/arch 違反） | Stage 1 FAIL | **Stage 2 不要、根本修正してから Stage 1 再実行** |
| IMPORTANT≥3 | Stage 1 FAIL | Stage 2 へ昇格 |
| NEEDS_DEEPER_REVIEW=true | Stage 1 FAIL | Stage 2 へ昇格 |

> Stage 1 CRITICAL は spec compliance 違反を意味するため、quality reviewer (Stage 2) を回しても無駄。修正後 Stage 1 から再実行する。

### Phase 3: Stage 2 — 全観点レビュー（FAIL 時のみ）

`auto-reviewing-pre-pr` の Phase 2 以降を実行。
収束判定・LLM-only 上限・ハードラウンド上限は同スキルに準拠。

### Phase 4: 最終報告

```markdown
## Sequential Review 結果

### 実施Stage
- Stage 1: 実行（PASS / FAIL）
- Stage 2: 実行 / スキップ

### Stage 1 内訳
（reviewer 別の検出件数）

### Stage 2 内訳（実行時のみ）
（auto-reviewing-pre-pr の最終報告と同形式）

### コスト試算
- Stage 1 のみ: tokens=X (約 $Y)
- Stage 1+2: tokens=X' (約 $Y')

### 判定
PR 作成可能 / 要追加修正
```

## 禁止事項

- Stage 1 で CRITICAL 残存のまま PR 作成
- Stage 1 を「念のためスキップ」して Stage 2 に直行（それなら auto-reviewing-pre-pr を使うべき）
- NEEDS_DEEPER_REVIEW=true を無視して Phase 4 へ進むこと
