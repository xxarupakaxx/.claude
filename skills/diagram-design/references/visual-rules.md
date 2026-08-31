# 共通視覚規則

## 役割トークン

値ではなく役割を参照する。

| role | 用途 |
|---|---|
| `paper` | ページ・node の背景 |
| `ink` | 本文、主線、主境界 |
| `muted` | 補助文、通常の矢印 |
| `soft` | sublabel、境界の説明 |
| `rule` | hairline |
| `accent` | 焦点1–2箇所 |
| `link` | 外部へ出る関係 |

既定の文字 stack は `-apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", "Noto Sans JP", system-ui, sans-serif`、技術ラベルは `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace` とする。remote font、`@import`、font download は使わない。

## SVG 順序

1. `<svg viewBox role="img" aria-labelledby="...">`
2. 直下の `<title>` と `<desc>`
3. inline `<style>` と `<defs>`
4. 背景、zone、connector、node、label、source note

node と重なる connector は node より先に描く。すべての visible text は shape や線だけに依存しない。

## connector

- off-axis は水平・垂直の直交 path。斜めの `<line>` は使わない。
- connector は丸い elbow（おおむね8px）で曲げ、label は紙色の mask を6–10px離して置く。
- 交差が避けられない場合は、意味の軽い線だけに小さな bridge を一つ付ける。二本とも bridge にしない。
- node の共有 attach point は12px以上離す。線を非終点 node の背後へ通さない。
- marker は endpoint ごとに一つ。`marker-start` は使わない。

## 密度と焦点

4px rhythm を基本にし、文字を縮めて一枚へ詰めない。accent は最重要の node、handoff、cycle など1–2要素だけに使う。shadow、glow、全 node の彩色、浮いた凡例、vertical writing mode は使わない。

Source basis: fixed upstream `SKILL.md` の anti-pattern、design system、connector rules。
