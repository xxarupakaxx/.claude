# theme · cobalt

技術資料を明るいpaper、cool ink、一本のblue signalで読む。コード・依存・statusが視覚の焦点になる。

~~~css
:root {
  --color-paper: oklch(98.5% 0.004 250);
  --color-ink: oklch(24% 0.02 258);
  --color-accent: oklch(58% 0.20 256);
  --radius-control: 0.375rem;
}
~~~

system sansとlocal monoを使い、外部fontを加えない。code panelは一つの証拠として使い、三つのequal cardへ分割しない。workbench、split-diptych、map-diagramと相性がよい。外部API、command palette、live fetchは既定にしない。
