---
name: cost-aware-llm
description: LLMコスト最適化。サブエージェントの model override を指定するか、親モデル継承に任せるかの判断ガイド。「コスト最適化して」「どのモデルを使うべき」等の依頼時に参照。詳細ルートは rules/model-routing.md に集約。
---

# Cost-Aware LLM Pipeline

サブエージェント起動時の **モデル選択判断スキル**。
Codex では通常 `model` を指定せず、親スレッドのモデル継承に任せる。明示指定が必要な場合だけ、タスク複雑度で `gpt-5.5` / `gpt-5.4` / `gpt-5.4-mini` を選ぶ。

詳細ルールは `~/.claude/rules/model-routing.md` に集約済み。本スキルは判断の起点として使う。

## クイック判断

```
明示指定が本当に必要？         → NO  → model未指定
タスクは検索/読み取りのみ？     → YES → gpt-5.4-mini
タスクは定形パターン適用？     → YES → gpt-5.4
セキュリティ/PRDレビュー？     → YES → gpt-5.5
タスクは複雑な判断を含む？     → YES → gpt-5.5
迷ったら                       → model未指定
```

## いつ呼ぶか

- ✅ サブエージェント起動前に「どのモデル？」と迷ったとき
- ✅ コスト最適化リクエスト（「もっと安く」「Opus 使いすぎでは」等）
- ❌ ルーチンレビュー（rules/model-routing.md に自動適用される）

## コスト削減 Tips

1. `MAX_THINKING_TOKENS=10000` で思考トークン制限（設定済）
2. `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` で早期 compact（設定済）
3. 並列 > 逐次（同情報を何度も渡すよりまとめて）
4. `/compact` を論理的ブレークポイントで

## 月間コスト目安

| パターン | 推定比 |
|----------|--------|
| すべて高精度モデル指定 | 100% |
| 親モデル継承 + 必要箇所のみ `gpt-5.4` | ~60% |
| 軽量調査のみ `gpt-5.4-mini` | ~40% |

## 関連

- `~/.claude/rules/model-routing.md` — 詳細な選択基準とサブエージェント別の割り当て
- Tier 1-3 レビューアーは各 agent 定義の懐疑姿勢とルーブリックで品質を担保する
