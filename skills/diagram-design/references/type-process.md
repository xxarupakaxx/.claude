# Process / data flow

担当をまたぐ処理は process、typed payload の受け渡しが中心なら data flow を使う。単なる順番なら process を使わず箇条書きか短い flowchart にする。

## 入力契約

```yaml
lanes:
  - {id: author, label: 仕様}
  - {id: builder, label: 実装}
  - {id: checker, label: 確認}
steps:
  - {id: inspect, label: 調査}
  - {id: build, label: 実装}
  - {id: verify, label: 検証}
nodes:
  - {lane: author, step: inspect, title: Sourceを読む, input: notes, output: brief, source: task:plan#L1-L8}
edges:
  - {from: [author, inspect], to: [builder, build], kind: handoff, source: task:plan#L9-L16}
```

lane は担当、step は順序、node は `(lane, step)` の作業を表す。空 cell は描かない。data flow では input / output の型を左右または上下に文字で表示し、色だけで payload を示さない。

## 構図

- 主軸を左→右の step とし、lane は水平帯で固定する。
- connector は横→縦の直交 path。source と destination の node を通り抜けない。
- 重要な handoff は一つだけ accent にし、通常線は muted、外部出力は link、制御 trigger は dashed にする。
- lane・step・node の label は2行以内。長い説明は本文へ移す。

## 上限

process は最大6 lanes / 12 steps、data flow は最大4 lanes / 6 steps。data flow の focal step・focal node・focal handoff は各1つ。上限を超えたら ingestion / analysis などに分割する。

## 再現性と出典

同じ入力は同じ viewBox・座標になるよう、生成時の入力を task artifact に残す。node と edge の source anchor を保ち、空 cell・unknown・除外を隠さない。`examples/process.*` は static fixture で、source-backed completion の証拠ではない。

Source basis: fixed upstream `references/type-process.md` と `references/type-data-flow.md`。
