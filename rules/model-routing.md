# Model Routing Rules

Agentツールでサブエージェントを起動する際に適用されるルール。

## Codexでの基本方針

`agents/*.md` の frontmatter には `model:` を書かない。
専門サブエージェントは親スレッドのモデルを継承させ、起動側が必要な場合だけ明示指定する。

Codex の `spawn_agent` で明示できる model override は以下のみ:

- `gpt-5.5`: 複雑な設計判断、セキュリティ分析、広範なレビュー
- `gpt-5.4`: 通常のコードレビュー、1-3ファイルの実装、テスト生成
- `gpt-5.4-mini`: grep結果の整理、単純な分類、軽量な読み取り調査

## 判断フロー

```
明示指定が本当に必要？ → NO → model未指定で親モデル継承
  ↓ YES
タスクは検索/読み取り中心？ → YES → gpt-5.4-mini
  ↓ NO
タスクは定形レビュー・小規模実装？ → YES → gpt-5.4
  ↓ NO
セキュリティレビュー or 複雑判断？ → YES → gpt-5.5
  ↓ NO
gpt-5.4
```

## 注意

- 迷ったら `model` を指定しない。
- `sonnet`, `opus`, `haiku` は Codex の `spawn_agent` では model override として使わない。
- Tier 1-3レビューアーは各 `agents/*.md` の評価姿勢とルーブリックで品質を担保する。
