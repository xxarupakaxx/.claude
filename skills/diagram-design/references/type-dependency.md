# Dependency graph

依存図は、tree では表せない共有依存（複数の親）または cycle を読ませるときだけ使う。全 node が一つの親で cycle もないなら tree または表へ戻す。

## 入力

```yaml
nodes:
  - id: renderer
    label: Renderer
    kind: internal | external | leaf
    rank: 1
    fan_in: 0
    source: repo:tools/example.py#L10-L22
edges:
  - from: renderer
    to: snapshot
    kind: runtime | build | external
    label: writes
    source: repo:tools/example.py#L24-L30
```

`id` は安定した module / package / service 単位にする。一ファイル一箱にしない。source が読めない場合は関係を追加しない。

## 構図

- rank 0 を上、依存の深い rank を下へ置く。通常線は下向きまたは同一 rank の水平線だけにする。
- node は角丸の箱、external は薄い境界、leaf は淡い fill。各 node に `依存 N` の fan-in を文字で表示する。
- cycle は最大1本だけ外周へ回し、`CYCLE` と明記する。cycle 以外の上向き線は禁止。
- connector を先に描き、node を後に描く。交差を避けられなければ rank または図を分ける。

## 上限

9 nodes、14 edges、4 ranks、強調 cycle 1つ。超過時は leaf cluster を `+N leaves` として統合し、caption と fidelity ledger に残す。

## SVG binding

```svg
<path data-from="renderer" data-to="snapshot" data-source="repo:path#L10-L22" d="M ... H ... V ..." />
<rect data-node-id="snapshot" data-rank="2" data-fan-in="2" />
<text data-node-id="snapshot" data-role="fan-in">依存 2</text>
```

線の `d` は水平・垂直 command だけで構成する。実際の数は source の証拠と一緒に保存し、デモデータをプロジェクトの事実と呼ばない。

## Before / candidate

Before は関係の平坦な列挙、candidate は rank・fan-in・共有依存が読める図として同じ item id を使う。Before の列挙から candidate が削除・統合したものを fidelity ledger に書く。`examples/dependency-before.*` と `examples/dependency-candidate.*` は構図検証用のデモであり、実プロジェクトの依存を表さない。

Source basis: fixed upstream `references/type-dependency.md`。
