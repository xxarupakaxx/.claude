---
name: cost-aware-llm
description: LLMコスト最適化。サブエージェントの model override を指定するか、親モデル継承に任せるかの判断ガイド。「コスト最適化して」「どのモデルを使うべき」等の依頼時に参照。詳細ルートは rules/model-routing.md に集約。
---

# Cost-Aware LLM Pipeline

サブエージェント起動時の **モデル選択判断スキル**。
現行の Codex `spawn_agent` は親モデル継承または `service_tier` なしの起動が失敗することがあるため、起動時は `model` と `service_tier` をペアで明示する。

詳細ルールは `~/.claude/rules/model-routing.md` に集約済み。本スキルは判断の起点として使う。

## クイック判断

```
タスクは検索/読み取りのみ？     → YES → model: gpt-5.4, service_tier: priority
タスクは定形パターン適用？     → YES → model: gpt-5.4, service_tier: priority
セキュリティ/PRDレビュー？     → YES → model: gpt-5.5, service_tier: priority
タスクは複雑な判断を含む？     → YES → model: gpt-5.5, service_tier: priority
迷ったら                       → model: gpt-5.4, service_tier: priority
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
| 通常タスクを `gpt-5.4` + `priority` に寄せる | ~60% |
| 複雑判断のみ `gpt-5.5` + `priority` に昇格 | ~70% |

## 関連

- `~/.claude/rules/model-routing.md` — 詳細な選択基準とサブエージェント別の割り当て
- Tier 1-3 レビューアーは各 agent 定義の懐疑姿勢とルーブリックで品質を担保する
