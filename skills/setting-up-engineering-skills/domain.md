# Domain 文書

engineering skill が codebase を調査するときに、この repo の domain 文書を読む方法を定める。

## 調査前に読むもの

- repo root の **`CONTEXT.md`**
- repo root に存在する場合は **`CONTEXT-MAP.md`**
このファイルは context ごとの `CONTEXT.md` を指すため、対象 topic に関係するものをすべて読む。
- **`docs/adr/`**
これから作業する領域に関係する ADR を読む。
multi-context repo では、context 単位の決定を確認するため `src/<context>/docs/adr/` も調べる。

これらのファイルが存在しない場合は、**何も言わずに先へ進む**。
ファイルがないことを問題として報告したり、最初から作成を提案したりしない。
`/grilling-with-docs` と `/improving-codebase-architecture` から呼び出される `/modeling-domains` skill は、用語や決定が実際に確定した時点で必要なファイルを作成する。

## ファイル構成

single-context repo（大半の repo）：

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-event-sourced-orders.md
│   └── 0002-postgres-for-write-model.md
└── src/
```

multi-context repo（root に `CONTEXT-MAP.md` が存在する場合）：

```
/
├── CONTEXT-MAP.md
├── docs/adr/                          ← system 全体の決定
└── src/
    ├── ordering/
    │   ├── CONTEXT.md
    │   └── docs/adr/                  ← context 固有の決定
    └── billing/
        ├── CONTEXT.md
        └── docs/adr/
```

## glossary の語彙を使う

出力内で domain concept に名前を付ける場合（issue title、refactor の提案、hypothesis、test name など）は、`CONTEXT.md` で定義された用語を使う。
glossary が明示的に避けている synonym へ逸脱しない。

必要な concept が glossary にない場合、それ自体が兆候である。
プロジェクトで使われていない言葉を作っているだけなら再考し、実際に不足しているなら `/modeling-domains` 用に記録する。

## ADR との矛盾を報告する

出力が既存の ADR と矛盾する場合は、黙って上書きせず明示する。

> _ADR-0007（event-sourced orders）と矛盾するが、次の理由から再検討する価値がある……_
