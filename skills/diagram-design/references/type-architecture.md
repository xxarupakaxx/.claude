# Architecture

system の component、主経路、trust boundary を読むための図。component が単なる階層なら dependency や layers、順序だけなら process を使う。

## 入力

```yaml
zones:
  - {id: authoring, label: 作成, boundary: local}
  - {id: runtime, label: 実行, boundary: local}
  - {id: evidence, label: 証拠, boundary: local}
components:
  - {id: plan, zone: authoring, label: 計画書, kind: source, source: task:30_plan.md#L1-L20}
links:
  - {from: plan, to: renderer, label: generates, style: primary, source: repo:scripts/generate.py#L10-L20}
```

## 構図

- zone は2つ以上の component を囲む薄い dashed boundary とし、label は境界を隠さない紙色 mask の上に置く。zone は最大3つ。
- 主経路の向き（左→右または上→下）を一枚で固定する。
- links は node より先に描く。主経路は solid、optional / return は dashed、forbidden は境界の手前で stop marker にする。
- 主経路または一つの gate だけを accent にする。全 component を accent にしない。

## connector の決め方

同じ軸なら `<line>`、軸が異なるなら水平・垂直の2 bend path。side port は主に水平接続、上下 port は主に垂直接続に使う。交差を避けられない場合は意味の軽い線だけに bridge を付ける。

## 上限と source

通常 overview は9 components / 12 links 以下、zone は3つ以下。詳細が必要なら zone ごとの detail に分ける。各 component・link に source anchor を持たせ、実装されていない runtime を図で「完了」と表示しない。`examples/architecture.*` は static fixture である。

Source basis: fixed upstream `references/type-architecture.md`。
