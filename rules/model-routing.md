# Model Routing Rules

Agentツールでサブエージェントを起動する際に適用されるルール。

## モデル選択基準

### Haiku (`model: "haiku"`)
- ファイル検索・パターンマッチ（Exploreサブエージェント）
- 単純な分類・振り分け
- learnings-researcher
- フォーマット変換

### Sonnet (`model: "sonnet"`)
- コードレビュー（Tier 1: arch-reviewer, perf-reviewer）
- コードレビュー（Tier 2-3: code-quality, test, error-handling, observability, a11y, ui-ux, concurrency, api-contract, docs, i18n, compliance, devops, rule-validator, code-simplicity）
- 1-3ファイルの実装
- テスト生成
- ドキュメント生成

### Opus（デフォルト、指定不要）
- **security-reviewer**（セキュリティ分析は常にOpus）
- **prd-reviewer**（要件との乖離検出は複雑な判断を伴う）
- アーキテクチャ設計
- 複数ファイルにまたがるデバッグ
- 10+ファイルのリファクタリング

## 判断フロー

```
タスクは検索/読み取りのみ？ → YES → haiku
  ↓ NO
タスクは定形パターンの適用？ → YES → sonnet
  ↓ NO
セキュリティレビュー or PRDレビュー？ → YES → opus
  ↓ NO
タスクは複雑な判断を含む？ → YES → opus
  ↓ NO
sonnet
```

## 注意

- 迷ったらsonnetを選択（コスパ最良）
- セキュリティ関連は必ずopus
- modelパラメータ未指定時はOpusが使われる
- Tier 1-3レビューアーは懐疑的評価姿勢+スコアリングルーブリック搭載済みのため、sonnetでも十分な品質を確保
