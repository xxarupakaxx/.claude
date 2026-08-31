# H2 · split diptych

主張と視覚的な証拠を横に置く構成。計画書のBefore / Afterでは左を観測事実、右を明示した移行案にする。

desktopは7/5または1/1の二列、gapは32px以上、panelの内側は24px以上を起点にする。各panelに固有の見出し、模型、caption、説明を持たせる。375pxでは一列へ移すが、本文を削らない。

~~~html
<section class="comparison-grid" aria-labelledby="comparison-title">
  <article class="compare-panel"><h3>Before｜観測</h3>…</article>
  <article class="compare-panel"><h3>After｜移行案</h3>…</article>
</section>
~~~
