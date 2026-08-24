# Typography system

## Font名より役割を決める

type systemには、少なくとも次のroleを置く。

- displayまたはpage title
- section heading
- body
- label
- supporting text
- action
- numericまたはcode

roleごとにfont family、size、weight、line height、letter spacing、case、colorを定義する。
同じvisual treatmentを異なる意味へ使わない。

## Fontを選ぶ条件

- brand voice
- 長文とUI labelの可読性
- 日本語を含む必要文字
- variable fontと必要weight
- numeral、currency、codeの扱い
- loading strategyとfallback metric
- license

「SaaSだからInter」「高級だからserif」といった分類だけで決めない。
既存brand fontがある場合は、代替する前に可読性、性能、glyph coverageの問題を示す。

## Scaleは情報階層から作る

固定のtype scaleを先に置かず、page title、section、body、dense dataの差を決める。
sizeだけでなく、weight、line height、space、colorを組み合わせる。

```css
:root {
  --text-caption: 0.75rem;
  --text-label: 0.8125rem;
  --text-body: 0.9375rem;
  --text-title: clamp(1.75rem, 1.35rem + 1.5vw, 2.75rem);
}
```

例の値は出発点であり、projectのbase sizeと利用環境に合わせる。
小さいlabelをuppercaseとwide trackingへ機械的に変換しない。日本語、長いlabel、screen magnificationで読みづらくなる場合がある。

## Measureとline heightを確認する

長文は読みやすいline lengthへ制限し、UI copyはcontrol幅に合わせてwrapまたは短縮する。
見出しはtight、本文はcomfortableを既定にできるが、fontのx-heightと日本語glyphで実画面確認する。

textをvertical centerへ置くときは、line boxではなくoptical alignmentも確認する。

## 数値とcodeを分ける

比較する数値にはtabular figuresを使う。

```css
.metric,
.table-number {
  font-variant-numeric: tabular-nums;
}
```

数値へmonospace fontを使う必要はない。
tabular figuresを持つ本文fontなら、brandと可読性を保ったままcolumnを揃えられる。

code、identifier、shortcutにはmono roleを用意し、本文全体へ広げない。

## Localizationと極端値で確認する

- 日本語とLatinのbaseline、weight、line heightが揃う。
- Germanなど長いlabel、CJKの改行、RTLのmirroringを対象範囲に応じて確認する。
- currency、percentage、negative value、large numberが崩れない。
- fallback fontへ切り替わってもlayout shiftとclippingが起きにくい。
- 200% text resizeでactionと情報が失われない。
