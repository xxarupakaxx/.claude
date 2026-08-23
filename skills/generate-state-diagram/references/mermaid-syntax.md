# SVG図の構文と安全性

このfileは旧path互換のため残している。
新しい図はSVGで生成する。

## 必須属性

- rootに `xmlns="http://www.w3.org/2000/svg"` と `viewBox` を置く。
- `role="img"`、`title`、`desc` を置く。
- nodeとedgeには安定したclassまたは `data-*` 属性を付ける。
- arrowは `marker`、関係名は `text` で表す。

## 禁止

- 外部script、外部font、外部image。
- `foreignObject`。
- `onload` などのevent handler属性。
- XMLとしてescapeしていない動的文字列。
- HTML内での実行時diagram変換。

## 可読性

長いlabelは複数の `tspan` に分ける。
edge labelには背景strokeを付け、線との重なりを避ける。
図と同じnodeとedgeの関係をtextでも残す。
