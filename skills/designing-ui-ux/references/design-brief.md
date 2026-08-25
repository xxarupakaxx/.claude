# Design brief

## Briefは判断の入力を固定する

Briefは見た目の注文書ではない。
誰が何を達成し、どの失敗を避け、どの情報を優先するかを固定する。

```md
## Product context
- Primary user:
- Situation:
- Job to be done:
- Success:
- Cost of failure:

## Task model
- Primary path:
- Frequent secondary paths:
- Critical edge cases:
- Destructive or irreversible actions:

## Information
- Must know now:
- Needed while acting:
- Can be deferred:
- Data extremes:

## Attention budget
- First question:
- Global orientation needed now:
- Global objects and relationships:
- Primary surface:
- Primary action:
- Always visible:
- On selection:
- On demand:
- Duplicate representations to remove:

## Experience
- Desired qualities:
- Existing constraints:
- Signature:
- Anti-signature:

## Evidence
- Existing screens or flows:
- Design system or components:
- Real data shapes:
- Acceptance criteria:
```

`Signature` は、利用者の仕事とブランドを同時に表す一つの特徴である。
装飾を一つ追加する欄ではない。
たとえば分析製品なら、他画面でも一貫して使える比較方法や注釈の仕組みが署名になり得る。

`Anti-signature` には、その製品らしさを壊す選択を書く。
医療画面で軽薄な成功演出を避ける、開発者向け画面で説明のために情報密度を落としすぎない、といった境界を置く。

## Task flowを画面より先に作る

各stepを次の形で記録する。

| Step | User intent | Required information | Action | System response | Recovery |
|---|---|---|---|---|---|
| 1 |  |  |  |  |  |

画面一覧は、この表を満たすために作る。
一つの画面へ複数stepを詰める場合は、利用者が同時に判断できる範囲か確認する。

## 状態はcomponent単位とflow単位で分ける

component stateには、default、hover、focus、pressed、selected、disabled、loading、errorを必要な範囲で置く。
flow stateには、first use、empty、partial data、permission denied、offline、conflict、success、recoveryを置く。

すべての状態を機械的に作る必要はない。
発生可能性と失敗コストから、必要な状態だけを選ぶ。

## 情報優先度を決める

情報を次の三層へ分ける。

1. **Orientation**：現在地、対象、状態。
2. **Decision**：次の判断に必要な比較、差、制約。
3. **Action**：実行、取消、復旧。

metadataと補助説明は、これらを妨げない位置へ置く。
cardやtabは情報構造を解決する道具であり、分類そのものではない。

## Attention budgetを決める

情報優先度を決めた後、初期画面で同時に見せる量を制限する。

- 最初に答える問いを一つにする。
- 主要surfaceを一つにする。
- primary actionを一つにする。
- Orientation、Decision、Actionのうち、現在のstepに不要な層を閉じる。
- 同じ状態を複数のcomponentで再掲しない。
- 全体の順序、範囲、現在位置が判断に必要なら、詳細を持たないcompact overviewを残す。
- Task以外の正本文書、判断、成果物が仕事を規定するなら、それらとの関係もoverviewへ含める。

component inventoryを次の表で確認する。

| Component | User question | Visibility | Remove or merge condition |
|---|---|---|---|
|  |  | always / selection / on-demand |  |

`User question`を書けないcomponentは、装飾か重複である可能性が高い。
別componentと同じ問いへ答える場合は統合を優先する。
OverviewとFocusがそれぞれ「全体のどこか」「いま何をするか」という異なる問いへ答える場合は、Overviewを補助情報として隠さない。

## 方向性は同じBriefから比較する

二案は色違いにしない。
情報密度、layout logic、type contrast、surface hierarchy、motion、signatureが異なる案にする。

| Decision | Direction A | Direction B | Briefとの適合 |
|---|---|---|---|
| Information density |  |  |  |
| Layout logic |  |  |  |
| Typography |  |  |  |
| Color role |  |  |  |
| Depth |  |  |  |
| Motion |  |  |  |
| Signature |  |  |  |
| Risk |  |  |  |

比較後は一案へ収束する。
両案の目立つ部分だけを混ぜると、設計原理が失われる。
