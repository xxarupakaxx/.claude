---
name: cost-aware-llm
description: LLMコスト最適化。サブエージェントに haiku/sonnet/opus を適切に割り当てる判断ガイド。「コスト最適化して」「どのモデルを使うべき」等の依頼時に参照。詳細ルートは rules/model-routing.md に集約。
---

# Cost-Aware LLM Pipeline

サブエージェント起動時の **モデル選択判断スキル**。
全タスクに Opus は不要。タスク複雑度で haiku/sonnet/opus を使い分けてコストを最適化する。

詳細ルールは `~/.claude/rules/model-routing.md` に集約済み。本スキルは判断の起点として使う。

## クイック判断

```
タスクは検索/読み取りのみ？     → YES → haiku
タスクは定形パターン適用？     → YES → sonnet
セキュリティ/PRDレビュー？     → YES → opus（必須）
タスクは複雑な判断を含む？     → YES → opus
迷ったら                       → sonnet (コスパ最良)
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
| 全 Opus | 100% |
| Opus + Sonnet サブエージェント | ~60% |
| Opus + Sonnet + Haiku | ~40% |

## 関連

- `~/.claude/rules/model-routing.md` — 詳細な選択基準とサブエージェント別の割り当て
- Tier 1-3 レビューアーは既に sonnet で十分な品質（懐疑姿勢+ルーブリック搭載済）
