# theme · grid

system、archive、依存関係を、near-whiteの紙、visible hairline、一本のsignal inkで示す。

~~~css
:root {
  --color-paper: oklch(99% 0.003 255);
  --color-ink: oklch(16% 0.010 255);
  --color-rule: oklch(88% 0.008 255);
  --color-accent: oklch(55% 0.21 28);
}
~~~

12列の線は必要な図や表の背面にだけ使い、本文の可読性を壊さない。radiusとshadowを増やさず、rule、余白、一本のplateで構造を示す。map-diagram、index-first、step-sequenceへ向く。計画書では巨大なlowercase displayを使わず、decisionが最初に読める見出しへ縮約する。
