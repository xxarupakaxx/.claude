# semantic color

色は装飾ではなく、paper、ink、rule、muted、accent、focus、positive、negativeという役割へ割り当てる。既存tokenがあれば再利用し、値をselectorへ散らさない。

~~~css
:root {
  --color-paper: #f7f8f5;
  --color-paper-raised: #ffffff;
  --color-ink: #17201b;
  --color-ink-muted: #526057;
  --color-rule: #c8d0c8;
  --color-accent: #0b6b58;
  --color-focus: #164fe5;
  --color-positive: #1c7046;
  --color-negative: #a03434;
}
~~~

白背景の小字、暗いpanelの薄字、focus ringは実画面でコントラストを測る。色を判定の唯一の手段にせず、label、記号、border、本文を併用する。accentは一つを基本にし、positive/negativeは状態の意味に必要な場合だけ使う。

## 選択

- 既存のdesign systemがある場合はそのpaletteとtoken名を守る。
- 新しいthemeは themes/catalog (themes/catalog.md) から一つだけ選ぶ。
- sourceで確認できないブランド色を「既存値」として扱わない。
- star数、流行、参考サイト名をthemeそのものへコピーしない。抽出するのは主軸、余白、type pairing、rule、構成である。
