# HTML レポートの形式

architectural review は、OS の temp directory に置く単一の self-contained HTML file として描画します。
TailwindはCDNから読みます。
diagramはgraph、sequence、mass diagram、cross-sectionを含めてinline SVGで描きます。
外部のdiagram runtimeは使いません。

## 雛形

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Architecture review — {{repo name}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
      /* small custom layer for things Tailwind doesn't cover cleanly:
         dashed seam lines, hand-drawn-feeling arrow heads, etc. */
      .seam { stroke-dasharray: 4 4; }
      .leak { stroke: #dc2626; }
      .deep { background: linear-gradient(135deg, #0f172a, #1e293b); }
    </style>
  </head>
  <body class="bg-stone-50 text-slate-900 font-sans">
    <main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
      <header>...</header>
      <section id="candidates" class="space-y-10">...</section>
      <section id="top-recommendation">...</section>
    </main>
  </body>
</html>
```

## ヘッダー

repo 名、日付、そして短い legend を置きます。
solid box = module、dashed line = seam、red arrow = leakage、thick dark box = deep module です。
導入 paragraph は要りません。
そのまま candidate へ入ります。

## 候補カード

diagram が主役です。
prose は少なく、平易に、そして `/designing-codebases` の glossary の語だけを自然に使います。

各 candidate は一つの `<article>` として作ります。

- **Title**。
  短く、deepening の内容が分かる名前にします。
  たとえば「Order intake pipeline を畳み込む」です。
- **Badge row**。
  recommendation strength は `Strong`、`Worth exploring`、`Speculative` のいずれかです。
  色は順に emerald、amber、slate を使います。
  さらに dependency category の tag も付けます。
  値は `in-process`、`local-substitutable`、`ports & adapters`、`mock` です。
- **Files**。
  `font-mono text-sm` で monospaced list にします。
- **Before / After diagram**。
  これが card の中心です。
  二列で左右に並べます。
  pattern は下を参照します。
- **Problem**。
  一文だけで、何が痛いのかを書きます。
- **Solution**。
  一文だけで、何が変わるのかを書きます。
- **Wins**。
  箇条書きにします。
  各 bullet は 6 語以下を目安にします。
  たとえば「Tests hit one interface」「Pricing logic stops leaking」「Delete 4 shallow wrappers」です。
- **ADR callout**。
  必要な場合だけ、amber 系の box で一行に収めます。

説明 paragraph は書きません。
diagram を理解するのに paragraph が必要なら、diagram を描き直します。

## 図のパターン

candidate に合う pattern を選びます。
一種類にそろえず、混ぜて使います。
すべての diagram を同じ見た目にしてはいけません。
variation 自体が point の一部です。

### SVGのgraph

dependencyやcall flowのように、「XがYを呼び、YがZを呼ぶ」という構造はinline SVGのnodeとedgeで描きます。
周囲は Tailwind の card で包み、diagram だけが唐突に浮かないようにします。
leakage edgeをred、deep moduleをdarkにします。
「beforeは往復6回、afterは1回」のようなcaseは、横方向のsequence SVGにします。

```html
<div class="rounded-lg border border-slate-200 bg-white p-4">
  <svg viewBox="0 0 720 180" role="img" aria-labelledby="graph-title graph-desc">
    <title id="graph-title">Order call flow</title>
    <desc id="graph-desc">OrderHandlerからOrderValidatorとOrderRepoを経てPricingClientへ漏れる依存関係。</desc>
    <!-- rect、path、textでnodeとedgeを描く -->
  </svg>
</div>
```

### 手組みの箱と矢印

moduleはSVGの `<rect>`、arrowは `<line>` または `<path>` で描きます。
after 側を、太い border を持つ一つの deep module として見せ、その内部を faded にしたいときは、この方法が向いています。

### 断面図

層状の shallow さを見せるのに向いています。
横帯を積み重ねます。
たとえば `h-12 border-l-4` を使います。
before では、何もしない薄い layer が 6 枚重なる姿を描きます。
after では、それらを一枚の厚い band に畳み込みます。

### 面積比較図

「interface の広さが implementation とほぼ同じだ」という shallow さを見せるのに向いています。
各 module に対して、interface の面積と implementation の面積を別 rectangle で描きます。
before では、interface rectangle が implementation rectangle とほぼ同じ高さになります。
after では、interface rectangle は短く、implementation rectangle は高くなります。

### 呼び出しグラフの折りたたみ

before では function call の tree を nested box で描きます。
after では、同じ tree を一つの box に collapse し、internal call は淡く box の内部へ残します。

## スタイル指針

- corporate dashboard より editorial 寄りにします。
  余白はたっぷり取ります。
  heading に serif を使うのは任意です。
  `font-serif` は stone と slate によく合います。
- 色は控えめに使います。
  accent は一色だけにし、emerald か indigo を使います。
  leakage は red、warning は amber にします。
- diagram の高さはおおむね 320px に保ちます。
  before / after が無理なく左右に収まるためです。
- diagram 内の module label には `text-xs uppercase tracking-wider` を使います。
  UI のラベルではなく schematic として読ませるためです。
- scriptはTailwind CDNだけにします。
  reportとdiagramはstaticに保ちます。
  app code や独自 interactivity は入れません。

## 最優先候補セクション

少し大きめの card を一つ置きます。
candidate 名、その理由を一文、その card への anchor link だけを書きます。
それ以上は不要です。

## 文体

文章は平易で簡潔にします。
ただし architectural noun と verb は `/designing-codebases` skill の語彙から外してはいけません。
簡潔さは drift の言い訳になりません。

**正確に使う語:** module、interface、implementation、depth、deep、shallow、seam、adapter、leverage、locality。

**言い換えない語:** component、service、unit（module の代わり）・API、signature（interface の代わり）・boundary（seam の代わり）・layer、wrapper（module の意味で使う場合）。

**この style に合う言い回しの例:**

- 「Order intake module is shallow — interface nearly matches the implementation.」
- 「Pricing leaks across the seam.」
- 「Deepen: one interface, one place to test.」
- 「Two adapters justify the seam: HTTP in prod, in-memory in tests.」

**Wins** の bullet は、glossary の語で gain を名指しします。
たとえば *「locality: bugs concentrate in one module」*、*「leverage: one interface, N call sites」*、*「interface shrinks; implementation absorbs the wrappers」* です。
*「easier to maintain」* や *「cleaner code」* は書きません。
それらは glossary にないうえ、言葉として弱すぎます。

hedging も throat-clearing も要りません。
「it's worth noting that…」のような前置きも不要です。
一文が bullet で済むなら bullet にします。
bullet がなくても伝わるなら削ります。
glossary にない語を使いたくなったら、まず glossary 内の語で言い換えられないかを考えます。
