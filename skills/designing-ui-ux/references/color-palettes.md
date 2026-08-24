# Color system

## 業界名からpaletteを決めない

fintech、healthcare、developer toolといった分類だけでは、brand、利用環境、情報密度、文化圏、既存資産を決められない。
固定の業界別paletteは候補探索に使えても、採用根拠にはしない。

## Semantic roleから組み立てる

```css
:root {
  --bg-canvas: ...;
  --bg-surface: ...;
  --bg-elevated: ...;
  --text-primary: ...;
  --text-secondary: ...;
  --text-disabled: ...;
  --border-default: ...;
  --border-strong: ...;
  --action-primary: ...;
  --action-primary-hover: ...;
  --focus-ring: ...;
  --status-info: ...;
  --status-success: ...;
  --status-warning: ...;
  --status-danger: ...;
}
```

raw color scaleとsemantic tokenを分ける。
componentは`blue-600`ではなく`action-primary`を参照する。

## Accentは役割を限定する

accentは、primary action、selection、link、focus、brand momentのどこへ使うかを決める。
複数の強いaccentを使う場合は、それぞれの意味が重ならないことを確認する。

status colorをbrand accentへ寄せすぎると、success、warning、dangerの識別が弱くなる。
色だけでstateを表さず、label、icon、shape、positionを組み合わせる。

## Lightとdarkを別々に調整する

dark modeはlight paletteの反転ではない。
surface間の差、text contrast、saturated colorのglow、border、image、chartを再調整する。

dark surface上の高彩度色は、面積が大きいほど視覚的に強くなる。
status backgroundとtextを別tokenにし、組合せごとにcontrastを測る。

## Paletteを選ぶ手順

1. 既存brand colorと利用禁止色を確認する。
2. canvas、surface、text、borderのneutral systemを先に作る。
3. primary actionとfocusの色を決める。
4. status colorsを意味ごとに決める。
5. light、dark、高contrastで確認する。
6. 実データ、disabled、selection、chartを並べて衝突を確認する。

generic blue、purple gradient、tealとcoralの組合せ自体を禁止しない。
Briefやbrandに根拠がなく、既製templateの印象だけを持ち込む使い方を避ける。
