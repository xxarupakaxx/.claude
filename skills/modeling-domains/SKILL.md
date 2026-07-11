---
name: modeling-domains
description: project の domain model を構築し、磨き続けます。 domain terminology や ubiquitous language を確定したいとき、architectural decision を記録したいとき、または別 skill が domain model の保守を必要とするときに使います。
---

# ドメインモデリング

設計を進めながら、project の domain model を能動的に作り込み、磨きます。
これは *active* な discipline です。
用語に異議を唱え、edge-case scenario を発明し、glossary と decision を固まった瞬間に書き留めます。
単に `CONTEXT.md` を読んで語彙を借りるだけなら、この skill ではありません。
それはどの skill でもやる一行習慣です。
この skill は model を **変える** ときに使い、ただ消費するだけのときには使いません。

## ファイル構成

多くの repo には一つの context しかありません。

```md
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

root に `CONTEXT-MAP.md` があるなら、その repo には複数 context があります。
map が、それぞれの場所を指します。

```md
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← system-wide decisions
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← context-specific decisions
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

file は lazy に作ります。
書くべきことができるまでは作りません。
`CONTEXT.md` がなければ、最初の用語が解決した時点で作ります。
`docs/adr/` がなければ、最初の ADR が必要になった時点で作ります。

## セッション中の振る舞い

### 用語集と照合して異議を出す

ユーザーが `CONTEXT.md` にある既存言語と衝突する語を使ったら、すぐに指摘します。
たとえば「glossary では cancellation を X と定義しているが、いま言っているのは Y に見える。 どちらなのか」と問い返します。

### 曖昧な言葉を鋭くする

曖昧だったり意味が過積載だったりする語が出たら、より正確な canonical term を提案します。
たとえば「account と言っているが、それは Customer なのか User なのか。 その二つは別概念だ」と詰めます。

### 具体的な場面で耐性確認する

domain relationship を話しているときは、具体 scenario で stress-test します。
edge case を突く scenario をこちらから発明し、concept 同士の境界を曖昧なままにしないようにします。

### コードと照合する

ユーザーが「こう動く」と言ったら、code が本当にそうなっているかを確認します。
食い違いがあれば、その場で表に出します。
たとえば「code は Order 全体を cancel しているが、いまの説明では partial cancellation が可能だと言っている。 どちらが正しいのか」と返します。

### `CONTEXT.md` をその場で更新する

用語が解決したら、その場で `CONTEXT.md` を更新します。
あとでまとめて書くのではなく、決まった瞬間に残します。
format は [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md) を使います。

`CONTEXT.md` には implementation detail を一切入れてはいけません。
`CONTEXT.md` を spec、scratch pad、implementation decision の置き場として扱ってはいけません。
これは glossary であり、それ以上でもそれ以下でもありません。

### ADR はむやみに勧めない

ADR を提案するのは、次の三つがすべて真のときだけです。

1. **Hard to reverse**。
2. **Surprising without context**。
3. **The result of a real trade-off**。

一つでも欠けるなら ADR は作りません。
format は [ADR-FORMAT.md](./ADR-FORMAT.md) を使います。
