# Model Routing Rules

Agentツールでサブエージェントを起動する際に適用されるルール。

## Codexでの基本方針

Codex `spawn_agent` では、通常 `model` と `service_tier` を省略し、親スレッドのモデル継承と各 agent role の既定値に任せる。
`service_tier` だけを指定すると、モデル解決経路によって `spawn_agent could not resolve the child model for service tier validation` で失敗することがあるため避ける。

Codex の汎用 `agent_type` は以下を使う:

- `explorer`: 読み取り専用のコードベース調査
- `worker`: 実装・修正などの実行作業
- `default`: 該当する専門ロールがない汎用タスク
- `arch-reviewer`, `security-reviewer`, `perf-reviewer` など: 専門レビュー

Claude Task 由来の `Explore` / `general-purpose` は Codex `spawn_agent.agent_type` ではないため指定しない。`learnings-researcher` は `~/.codex/agents/` に定義済みだが、このセッションの tool schema に未ロードなら `rg`/SQLite または `explorer` で代替する。

明示的なモデル昇格が必要な場合のみ、以下の有効なペアを使う:

- `model: gpt-5.5`, `service_tier: priority`: 複雑な設計判断、セキュリティ分析、広範なレビュー
- `model: gpt-5.4`, `service_tier: priority`: 明示的に標準モデルへ固定したいレビュー・実装・読み取り調査

## 判断フロー

```
通常は model/service_tier を省略
  ↓ 明示的な昇格が必要？
セキュリティレビュー or 複雑判断？ → YES → gpt-5.5 + priority
  ↓ NO
明示的に標準モデルへ固定したい？ → YES → gpt-5.4 + priority
  ↓ NO
model/service_tier を省略
```

## 注意

- 迷ったら `model` / `service_tier` を省略する。
- `service_tier` だけを指定しない。
- `gpt-5.4-mini` に `service_tier: priority` は指定しない。
- `sonnet`, `opus`, `haiku` は Codex の `spawn_agent` では model override として使わない。
- Tier 1-3レビューアーは各 `~/.codex/agents/*.toml` の評価姿勢とルーブリックで品質を担保する。
