---
name: sequential-review-pre-pr
description: delivery前の変更を Stage 1 の spec/rule/architecture 確認から始め、必要なときだけ Stage 2 の全観点レビューへ昇格する。`/sequential-review-pre-pr`、「2段階レビューして」「Stage1から」で使う。
context: current
---

# Sequential Review Pre-PR

実装後、PR作成前の spec compliance と品質確認を段階的に行う。Approved PRD と Evidence Bundle の整合性を確認するが、PRD 自体の承認は `prd-reviewer` の担当である。

## 使い分け

- 軽微〜中規模、段階的に確認したい変更：この skill
- 大規模、security/performance critical、最初から全観点が必要：`auto-reviewing-pre-pr`

## 1. Stage を選ぶ

```bash
git diff $BASE_BRANCH --stat
```

| 変更 | 動作 |
| --- | --- |
| 1〜3 files かつ <50 LOC | Stage 1 のみを提案 |
| 4〜9 files | Stage 1、結果に応じ Stage 2 |
| 10 files 以上 | `auto-reviewing-pre-pr` を推奨し、この skill では Stage 2 まで行う |

明示的にこの skill が呼ばれた場合は上の判定に従う。小規模変更へ別の全観点 reviewer が既に指定された場合は、Stage 1 を飛ばさず本 skill の理由を伝える。

## 2. Stage 1

変更 risk に含まれる場合だけ `Task` で次を並列起動する。

- `rule-validator`：`CLAUDE.md` と `rules/`
- `arch-reviewer`：architecture 整合性

各 reviewer に、重大問題または広範なレビューが必要なら出力末尾へ `NEEDS_DEEPER_REVIEW: true` と書くよう伝える。

判定は次のとおり。

- `CRITICAL=0`、`IMPORTANT≤2`、`NEEDS_DEEPER_REVIEW=false`：Stage 1 PASS、最終報告へ。
- `CRITICAL≥1`（spec/rule/arch 違反）：FAIL。まず根本修正し、Stage 1 を再実行する。修正前に Stage 2 や PR 作成へ進まない。
- `IMPORTANT≥3` または `NEEDS_DEEPER_REVIEW=true`：FAIL。Stage 2 へ昇格する。

## 3. Stage 2

Stage 1 が FAIL で、CRITICAL の修正待ちでない場合だけ `auto-reviewing-pre-pr` の Phase 2 以降を実行する。収束判定、LLM-only 上限、hard round 上限は同 skill に従う。

## 4. 最終報告

実施した Stage と PASS/FAIL、reviewer 別の検出件数、Stage 2 の結果（実行時）、修正要否を報告する。CRITICAL、IMPORTANT、`NEEDS_DEEPER_REVIEW` の状態を省略せず、根拠と未実施の確認を分ける。

## 禁止

- Stage 1 の CRITICAL を残したまま PR を作成する。
- `NEEDS_DEEPER_REVIEW=true` を無視して完了にする。
- Stage 1 を「念のため」省略して Stage 2 へ直行する。その場合は `auto-reviewing-pre-pr` を使う。
