---
name: cost-aware-llm
description: LLMコスト最適化。サブエージェントの model override を指定するか、親モデル継承に任せるかの判断ガイド。「コスト最適化して」「どのモデルを使うべき」等の依頼時に参照。詳細ルートは rules/model-routing.md に集約。
---

# Cost-Aware LLM Pipeline

サブエージェント起動時の **モデル選択判断スキル**。
コストを下げるときは、モデルを下げる前に agent の起動自体を減らす。
明示指定が必要な場合は、`haiku`、`sonnet`、`opus` の責務を混ぜない。

詳細ルールは `~/.claude/rules/model-routing.md` に集約済み。本スキルは判断の起点として使う。

## クイック判断

```
shell、Grep、Glob、diffで完結する？       → YES → L0 local
短い低リスクhelperで、leadが即検査できる？ → YES → L1 haiku
探索・routine実装・通常ワーカー？          → YES → L2 sonnet
計画・重要判断・レビュー？                 → YES → L3 opus
迷ったら                                   → model省略、または一段上へ昇格
```

## いつ呼ぶか

- ✅ サブエージェント起動前に「どのモデル？」と迷ったとき
- ✅ コスト最適化リクエスト（「もっと安く」「Opus 使いすぎでは」等）
- ❌ ルーチンレビュー（rules/model-routing.md に自動適用される）

## コスト削減の順序

1. shell、Grep、Glob、既存 script で処理し、不要な agent を起動しない。
2. 独立した読み取りだけを並列化する。
3. agent へ全文を渡さず、objective、scope、acceptance、prior failure、output だけを渡す。
4. commit文案、短い要約、定型整形、重複検出だけを `haiku` に任せる。
5. 探索と routine 実装は `sonnet`、計画と重要判断とレビューは `opus` に保つ。

## Haikuのガードレール

`haiku` は短い入力と短い出力で完結し、lead がすぐ検査できる場合だけ使う。
不確実性、矛盾、複数ファイルにまたがる判断、外部副作用、ユーザー影響が出たら、その round を止めて `sonnet` または `opus` へ昇格する。
設計、セキュリティ、GO/NO-GO、専門レビュー、最終判定には使わない。

実際の `git add`、`git commit`、`git push` は shell で実行する。
commit に関して `haiku` が担当できるのは、git-cz形式のメッセージ文案だけである。

## 削減レバー

| レバー | 削減対象 | 守るもの |
|---|---|---|
| local処理を優先 | agent起動数 | 機械検証の正確さ |
| Context Slimming | 入力token | 合格基準と直近の失敗原因 |
| `haiku`限定投入 | 軽量helperの単価 | 設計・実装・レビューの品質 |
| 並列化 | 待ち時間と背景の再送 | 依存関係とwrite scope |

## 関連

- `~/.claude/rules/model-routing.md` — 詳細な選択基準とサブエージェント別の割り当て
- Tier 1-3 レビューアーは各 agent 定義の懐疑姿勢とルーブリックで品質を担保する
