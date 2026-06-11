# Model Routing Rules

Agentツールでサブエージェントを起動する際に適用されるルール。

## Codexでの基本方針

`~/.codex/agents/*.toml` には `model` と `service_tier` を必ず書く。
現行の Codex `spawn_agent` では、親モデル継承または `service_tier` なしの起動が
`spawn_agent could not resolve the child model for service tier validation` で失敗することがある。
当面は起動側で `model` と `service_tier` を必ずペア指定する。

Codex の `spawn_agent` で利用する model/service_tier は以下に限定する:

- `model: gpt-5.5`, `service_tier: priority`: 複雑な設計判断、セキュリティ分析、広範なレビュー
- `model: gpt-5.4`, `service_tier: priority`: 通常のコードレビュー、1-3ファイルの実装、テスト生成、軽量な読み取り調査

## 判断フロー

```
タスクは検索/読み取り中心？ → YES → gpt-5.4 + priority
  ↓ NO
タスクは定形レビュー・小規模実装？ → YES → gpt-5.4 + priority
  ↓ NO
セキュリティレビュー or 複雑判断？ → YES → gpt-5.5 + priority
  ↓ NO
gpt-5.4 + priority
```

## 注意

- 迷ったら `model: gpt-5.4`, `service_tier: priority` を指定する。
- `gpt-5.4-mini` は `priority` 非対応で、service tier 未指定経路が失敗するため当面使わない。
- `sonnet`, `opus`, `haiku` は Codex の `spawn_agent` では model override として使わない。
- Tier 1-3レビューアーは各 `~/.codex/agents/*.toml` の評価姿勢とルーブリックで品質を担保する。
