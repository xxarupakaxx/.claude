# theme · brutal

強いruleと平面の色で、変更点・制約・失敗経路をすぐ読む。装飾ではなく境界の明示が目的。

~~~css
:root {
  --color-paper: #f4f4ef;
  --color-ink: #151515;
  --color-rule: #151515;
  --color-accent: #d94335;
  --radius-control: 0;
}
~~~

太いruleは段階・差分・停止条件へ使い、全要素をbox化しない。step-sequence、workbench、comparisonへ向く。警告をaccentだけで表さず、「未確認」「公開停止」など本文labelを併記する。
