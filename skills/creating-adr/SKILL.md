---
name: creating-adr
description: ADR（Architecture Decision Record）を作成・更新する。技術的意思決定を記録したいとき、アーキテクチャ選定の理由を残したいとき、複数の選択肢を比較検討したいときに使用。
---

# Creating ADR

技術的意思決定を構造化されたADRフォーマットで記録する。

## トリガー条件

以下のような依頼で自動的に使用:
- 「ADRを作成して」「意思決定を記録して」
- 「なぜこの技術を選んだか記録して」
- 「アーキテクチャ決定を文書化して」
- 技術選定や設計判断の比較検討を依頼されたとき

## ワークフロー

### Step 1: 情報収集

以下の情報を確認（不足があればAskUserQuestionで確認）:

1. **決定事項**: 何を決定するのか
2. **背景・目的**: なぜこの意思決定が必要か
3. **選択肢**: 検討した選択肢（最低2つ）
4. **評価軸**: 比較するための観点

### Step 2: 選択肢の比較分析

各選択肢について:
- Pros（メリット）を列挙
- Cons（デメリット）を列挙
- 比較表を作成

### Step 3: ADR作成

以下のテンプレートでADRを作成:

```markdown
# ADR-XXX: [タイトル]

**Status**: [Proposed | Accepted | Deprecated | Superseded]
**Date**: YYYY-MM-DD
**Deciders**: [関係者]

## Context

意思決定の背景、及び目的

### References

- [参考資料へのリンク]

## Considered Options

今回の意思決定をするにあたって、複数の選択が存在した場合は、ここに列挙

### Comparison Table

|  | Option A | Option B |
| --- | --- | --- |
| Feature 1 |  |  |
| Feature 2 |  |  |

### Option A

👍 **Pros**

-

👎 **Cons**

-

### Option B

👍 **Pros**

-

👎 **Cons**

-

## Discussion

意思決定するにあたって議論があればここに書く

## Decision

具体的に決定した内容

## Consequences

上記の決定による影響および懸念事項
```

### Step 4: 配置先の決定

ADRファイルの配置先を確認:
1. `docs/adr/` が存在する場合 → そこに配置
2. `docs/decisions/` が存在する場合 → そこに配置
3. 上記がない場合 → AskUserQuestionで配置先を確認

**命名規則**: `NNNN-<タイトル>.md`（例: `0001-use-kysely-for-orm.md`）

## ADRのステータス

| Status | 説明 |
|--------|------|
| Proposed | 提案中、レビュー待ち |
| Accepted | 承認済み、適用中 |
| Deprecated | 非推奨、別の決定に置き換え予定 |
| Superseded | 新しいADRに置き換え済み |

## 注意事項

- 比較表は評価軸を明確にし、客観的に記載
- Consequences は良い影響・悪い影響の両方を記載
- 将来の参照者が「なぜ」を理解できるように背景を詳しく記載
