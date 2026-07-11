---
name: choosing-skills
description: いまの状況に合う skill や flow を選ぶための案内役です。 このリポジトリ内の skills を横断して適切な流れに振り分けます。
disable-model-invocation: true
---

# スキル選択ガイド

全部の skill を覚えていなくても大丈夫なので、迷ったらここで選びます。

**flow** とは、複数 skill を通る進行ルートのことです。
多くのルートは一つの **main flow** に沿って進み、そこへ二つの **on-ramp** が合流します。
それ以外は standalone か、その下支えになる語彙レイヤーです。

## 主ルート: 発想から出荷まで

もっとも多くの仕事が通るルートです。
アイデアがあり、それを実装したいときに使います。

1. **`/grilling-with-docs`** で対話しながらアイデアを研ぎ澄まします。
コードベースが **ある** 場合はここから始めます。
この flow は stateful で、`CONTEXT.md` や ADR に学んだ内容を残していきます。
コードベースがないなら `/grill-me` を使います。
どちらも同じ `/grilling` を中核に使いますが、記録を残すのは `grilling-with-docs` です。
2. **分岐: 会話だけで答えを確定できるか。**
実行して確かめる必要がある問いなら、`/handing-off-context` を往復の橋にして prototype に寄り道します。
   - まず **`/handing-off-context`** で文脈を外へ渡します。
   - そのファイルを使って新しいセッションを開きます。
   - **`/prototyping-solutions`** で捨てる前提のコードを作り、問いに答えます。
   - 学んだことを **`/handing-off-context`** で元のアイデアスレッドへ戻します。
3. **分岐: 複数セッションにまたがる実装か。**
   - **はい** → **`/writing-specifications`** でスレッドを spec に変換し、そのあと **`/creating-tracer-tickets`** で tracer-bullet 形式の ticket に分割します。
   - local tracker なら、ticket は `.scratch/<feature>/issues/` 以下に 1 ファイルずつ作られ、blocker から順に手で進めます。
   - real tracker なら blocking edge はネイティブな依存リンクになります。
   - blocker が片付いた ticket から順に **`/implementing-work`** を起動し、**各 ticket ごとに文脈をクリアして** 実装します。
   - **いいえ** → このまま同じ文脈ウィンドウ内で **`/implementing-work`** に進みます。

どちらの分岐でも、**`/implementing-work`** は各 issue を **`/tdd`** で 1 スライスずつ進めます。
実装が終わったら **`/reviewing-code`** を使い、diff を Standards と Spec の 2 軸でレビューしてから commit します。
完全な spec までは要らず、具体的な振る舞いを test-first で作りたいだけなら **`/tdd`** 単体で使います。
branch や PR を固定点に対してレビューしたいだけなら **`/reviewing-code`** 単体で使います。

### コンテキスト衛生

手順 1〜3 は **一つの連続した文脈ウィンドウ** の中で進めます。
`/creating-tracer-tickets` を終えるまでは compact も clear もしません。
grilling、spec、ticket が同じ思考の流れの上に積み上がるためです。
その後の各 `/implementing-work` は、ticket を起点に fresh な文脈で始めます。

この運用の上限は **[smart zone](https://www.aihero.dev/ai-coding-dictionary/smart-zone)** です。
これは、最先端モデルが鋭く推論できる文脈ウィンドウの範囲を指します。
`/creating-tracer-tickets` 前にその上限へ近づいたら、質が落ちたまま押し切らず、`/handing-off-context` で引き継いで fresh なスレッドに移ります。

## 合流ルート

特定の出発状況から始まり、その後 main flow に合流する入り口です。

- **バグや依頼が溜まっている** → **`/triaging-issues`**。
  triage role を通して issue を agent-ready な形に整え、あとで **`/implementing-work`** が拾います。
  triage の対象は **自分で作っていない issue** だけです。
  bug report、流入した feature request、未整理の依頼が対象です。
  `/creating-tracer-tickets` が作った ticket はすでに agent-ready なので、**再 triage しません。**

- **何かが壊れている** → **`/diagnosing-bugs`**。
  これは、一目で原因が分からないバグ、断続的な flake、既知の正常状態の間に紛れ込んだ regression 向けです。
  **このバグで確実に赤くなる一つの command** という tight feedback loop ができるまでは仮説を立てません。
  そのうえで regression test を添えて直します。
  事後分析の結果、「バグを閉じ込める seam 自体がない」が本質なら、**`/improving-codebase-architecture`** へ受け渡します。

- **巨大で霧が深い取り組みで、一つのセッションには収まらない** → **`/mapping-large-projects`**。
  greenfield project や巨大 feature build のように、ここからゴールまでの道筋がまだ見えていないときに使います。
  issue tracker 上に investigation ticket の **共有マップ** を描き、deliverable ではなく **decision** を一つずつ積み上げて霧を晴らします。
  道筋が見えたら **`/writing-specifications`** に合流します。
  規模が思ったより小さいと分かったなら、そのまま **`/implementing-work`** へ進みます。
  **`/grilling-with-docs`** が一つのセッションで抱えられるアイデアを磨くものだとすれば、wayfinder は一つのセッションでは抱えきれないアイデアのためのものです。

## コードベース健全性

feature work ではなく、保守のための lane です。

- **`/improving-codebase-architecture`**。
  余力があるときに実行し、agent が動きやすい codebase を保ちます。
  ここでは **deepening opportunity** を掘り起こします。
  一つ選ぶと、それ自体が `/grilling-with-docs` に持ち込める **アイデア** になります。
  候補を発見するのが survey の役目で、選んだ候補の形を設計する bench が **`/designing-codebases`** です。

## 下支えの語彙レイヤー

他の skill の **下で** 動く model-invoked の参照系が二つあります。
どちらも、それぞれの語彙に関する single source of truth です。
問題が process ではなく **言葉** にあるときは直接使います。
普段は上位 skill が必要に応じて呼び込みます。

- **`/modeling-domains`**。
  project の *domain* language を磨きます。
  曖昧な語を問い直し、過積載の語を分解し、後戻りしづらい判断を ADR として記録します。
  `/grilling-with-docs` が `CONTEXT.md` をきれいな glossary に保つために使う、能動的な discipline です。
- **`/designing-codebases`**。
  module の *shape* を設計するための deep-module vocabulary を提供します。
  小さな interface の裏に大きな振る舞いを置き、きれいな seam に載せるための考え方です。
  `/tdd` と `/improving-codebase-architecture` もこの語彙を使います。

## セッションをまたぐとき

- **`/handing-off-context`**。
  スレッドがいっぱいになったときや、たとえば `/prototyping-solutions` 用に別セッションへ分岐したいときに使います。
  会話を markdown ファイルへ圧縮し、そのファイルを参照して新しいセッションへ文脈を運びます。
  その場で続けるのではなく、**新しいセッションを開いてそのファイルを渡す** のが前提です。
  fresh なセッションが欲しいが、現在の会話は残したいときに使います。
- **`/compact`**（built-in）。
  こちらは **同じ会話の中** に残り、先行ターンを要約に置き換えるためのものです。
  phase の切れ目のような、意図的な区切りで使います。
  phase の途中で compact してはいけません。
  agent が道を見失いやすくなるためです。
  `/handing-off-context` は分岐で、`/compact` は継続です。

## 単独で使うもの

main flow から外れて単独で使うものです。

- **`/grill-me`**。
  `/grilling-with-docs` と同じくらい容赦なく聞きますが、**codebase がない** とき用です。
  stateless で、ローカルに何も保存せず、`CONTEXT.md` も作りません。
  repo に属さない plan や design を鍛えるときに使います。
- **`/prototyping-solutions`**。
  一つの design question に答えるための小さな捨てコードです。
  state model がしっくり来るか、UI をどう見せるべきか、といった問いに使います。
  最初から throwaway と割り切り、答えだけを残してコードは捨てます。
  main flow の手順 2 に出てくる寄り道ですが、紙の上だけでは決めきれない design question があるときは単独でも使えます。
- **`/research`**。
  読み込み作業を **background agent** に委譲します。
  一次情報に当たって調べたうえで、引用付き Markdown ファイルを repo に残します。
  調査中も自分の作業は続けられます。
  そこでできたファイルは、`/grilling-with-docs` に持ち込む材料であり、思考そのものの代わりではありません。
- **`/teaching-concepts`**。
  current directory を stateful workspace として使いながら、複数セッションにまたがって概念を学ぶときに使います。
- **`/writing-great-skills`**。
  skill をうまく書いたり編集したりするための参照です。

## 事前条件

**`/setting-up-engineering-skills`** は、最初の engineering flow に入る前に実行します。
ここで、他の skill が前提にしている issue tracker、triage label、doc layout を設定します。
custom issue tracker にも対応できます。
