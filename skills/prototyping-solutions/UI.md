# UI プロトタイプ

一つの route 上に **根本的に異なる複数の UI variation** を作り、floating bottom bar で切り替えられるようにします。
ユーザーは browser 上で variant を行き来し、一つを選ぶか、各案の良いところを持ち寄ります。
残りは捨てます。

問いが logic や state に関するものなら branch が違います。
[LOGIC.md](LOGIC.md) を使います。

## これが適した形である場面

- 「この page はどう見えるべきか。」
- 「この dashboard を決める前に、数案を見たい。」
- 「settings screen の layout を別方向で試したい。」
- 頭の中の曖昧な mockup を三つ並べて一日悩む代わりに、実物で比較したい場面全般。

## 二つの形

強く推奨するのは sub-shape A です。

UI prototype は、**app の既存部分にぶつけて見たほうが** 判断しやすくなります。
実際の header、sidebar、data、density があるからです。
単独の throwaway route は真空に近く、どの variant も単体では良く見えてしまいます。
variant を載せられそうな既存 page があるなら、基本は sub-shape A を選びます。
本当に近い置き場がないときだけ sub-shape B を使います。

### 形 A

既存 page を調整する形です。
route 自体はそのままで、render する subtree だけを variant ごとに切り替えます。
切り替えは `?variant=` の URL search param で行います。
既存の data fetching、param、auth はそのまま残します。
これが既定です。
よほどの理由がなければこちらを選びます。

まだ page が存在しなくても、自然に既存 page の内側へ入るものなら、なお sub-shape A です。
たとえば dashboard の新 section、settings screen の新 card、既存 flow の一 step などです。
その場合は host page の中へ variant を mount します。

### 形 B

新 page を立てる形です。
これを使うのは、prototype 対象が本当に既存 page のどこにも自然に載らないときだけです。
完全な top-level surface や、どこへも埋め込めない flow が該当します。

project の既存 routing convention に従って **throwaway route** を作ります。
新しい top-level structure を invent してはいけません。
path か filename のどこかに `prototype` を含め、prototype だと一目で分かる名前にします。
`?variant=` の仕組みは同じです。

sub-shape B を選ぶ前に、本当に既存 page へ埋め込めないのかを sanity-check します。
空の route では、本来なら露出する design problem が隠れてしまうからです。

どちらの sub-shape でも、floating bottom bar の仕様は同じです。

## 手順

### 1. 問いを明文化し、N を決める

既定は **3 variant** です。
5 を超えると radically different な比較ではなく、noise になりがちです。
そこで打ち止めにします。

plan は一行で書き残します。
場所は prototype の近くでも、file 冒頭 comment でも構いません。

> 「既存の `/settings` route 上で、`?variant=` により切り替えられる settings page の 3 variant を作る。」

ユーザーがその場にいて反応してくれる場合でも、いない場合でも、これは書いておきます。

### 2. 根本的に異なる variant を作る

各 variant を起こします。
すべて次の制約の中で作ります。

- page の目的に沿っていること。
- その page が持てる data の範囲内であること。
- project の component library や styling system に従うこと。
- export 名が明確であること。

component 名は `VariantA`、`VariantB`、`VariantC` のように分かりやすくします。

variant は **構造が違って** いなければいけません。
layout、information hierarchy、primary affordance が違う必要があります。
色だけ違う、copy だけ違う、というのは variant ではありません。
少し調整した card grid が三つ並ぶだけなら、それは prototype ではなく wallpaper です。
二案が似過ぎたら、「card grid を使わない」など明示的な制約を付けて片方を作り直します。

### 3. 一つに束ねる

route 上に一つの switcher component を置きます。

```tsx
// pseudo-code — adapt to the project's framework
const variant = searchParams.get('variant') ?? 'A';
return (
  <>
    {variant === 'A' && <VariantA {...data} />}
    {variant === 'B' && <VariantB {...data} />}
    {variant === 'C' && <VariantC {...data} />}
    <PrototypeSwitcher variants={['A','B','C']} current={variant} />
  </>
);
```

sub-shape A では、既存 page 側の data fetching を switcher より上に残します。
variant ごとに変えるのは rendered subtree だけです。

sub-shape B では、`/prototype/<name>` の throwaway route が同じ switcher を mount します。

### 4. 浮動 switcher を作る

画面下中央に固定表示する小さな bar を作ります。
構成要素は三つです。

- **Left arrow**。
  前の variant に進みます。
  最初まで行ったら末尾へ wrap します。
- **Variant label**。
  現在の variant key を表示します。
  variant 側が name を export しているなら、その名前も併記します。
  たとえば `B — Sidebar layout` のようにします。
- **Right arrow**。
  次の variant に進みます。
  末尾まで行ったら先頭へ wrap します。

振る舞いは次のとおりです。

- arrow を click したら URL search param を更新します。
  framework の router を使います。
  Next なら `router.replace`、React Router なら `navigate` などです。
  variant を share でき、reload 後も同じ状態に戻る必要があります。
- keyboard でも `←` と `→` で切り替えます。
  ただし `<input>`、`<textarea>`、`[contenteditable]` に focus があるときは intercept しません。
- 見た目は page 本体と明確に区別します。
  high-contrast な pill や subtle な shadow を使い、評価対象の design そのものだと誤解されないようにします。
- production build では hidden にします。
  `process.env.NODE_ENV !== 'production'` か、それに相当する check で gate し、うっかり merge しても bar が user に見えないようにします。

switcher は一つの shared component にまとめます。
両 sub-shape が再利用できるようにし、project の shared UI 置き場へ置きます。

### 5. ユーザーへ渡す

URL と `?variant=` の key を共有します。
ユーザーは都合のよいときに見比べます。
たいてい有益なのは、「header は B、sidebar は C が良い」のような feedback です。
それが、ユーザーが本当に欲しい design です。

### 6. 答えを残して片付ける

winner が決まったら、どの variant が勝ち、なぜそう判断したかを先に残します。
そのあとで、[SKILL](SKILL.md) に書かれた方法で prototype 自体も捕捉します。
winner は real code に fold します。
それ以外は main ではなく throwaway branch 側へ移します。

- **Sub-shape A**。
  winner を既存 page に fold し、負けた variant と switcher は main から落とします。
- **Sub-shape B**。
  winner を real route に昇格させ、throwaway route と switcher は main から落とします。

variant 一式そのものが primary source です。
だから bin に捨てず、throwaway branch に残します。
main branch に置きっぱなしの variant component や switcher は、すぐ腐って次の reader を混乱させます。

## アンチパターン

- **色や copy しか違わない variant**。
  それは tweak であって prototype ではありません。
  本物の variant は構造で食い違います。
- **variant 間で code を共有し過ぎること**。
  shared な `<Header>` 程度なら構いません。
  しかし shared な `<Layout>` まで共通化すると point が消えます。
  各 variant が layout ごと捨てられる自由を残します。
- **real mutation に配線すること**。
  read-only prototype で十分です。
  mutation が必要なら stub に向けます。
  問いは「どう見えるべきか」であって、「backend が動くか」ではありません。
- **prototype をそのまま production に昇格させること**。
  variant code は prototype 制約のもとで書かれています。
  test も薄く、error handling も最小です。
  fold するときは proper に書き直します。
