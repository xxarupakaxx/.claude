# 日本語の文字組み

font名の指定より、既存のlocal/system stack、字幅、行間、見出しの階層を先に決める。外部fontを読み込まない。

## 起点

~~~css
:root {
  --font-body: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI",
    "Hiragino Sans", "Yu Gothic", sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  --text-body: 1rem;
  --leading-body: 1.85;
  --text-small: 0.8125rem;
  --text-h2: clamp(1.35rem, 2.2vw, 1.75rem);
  --text-h1: clamp(1.9rem, 3.4vw, 2.5rem);
}
body {
  font-family: var(--font-body);
  font-size: var(--text-body);
  line-height: var(--leading-body);
}
~~~

日本語本文は15–17px、1.75–1.95を起点にし、長いpathはmonoと折返しを使う。ひらがな・漢字の連続をletter-spacingだけで詰めない。

## 階層

- h1は文書のdecisionを短く示し、最大40px前後から始める。
- h2は26–28px程度、h3は20–22px程度から始める。
- labelは本文より小さくしても、muted色だけに頼らず文字と位置で読めるようにする。
- code、path、source idは overflow-wrap: anywhere と white-space: pre-wrap を使い、視野外へ押し出さない。
- 見出しと本文の間を狭く、節の間を広くする。行間の不足をpaddingだけで補わない。

## 禁止

巨大displayをheroの代わりに使わない。斜体、意味のない全大文字、外部font link、未確認のfont性能を既定にしない。見出しの文言をCSSで隠したり変形したりせず、読み上げる文字を保つ。
