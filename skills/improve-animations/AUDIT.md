# アニメーション監査プレイブック

8つの監査カテゴリと、各カテゴリで確認する内容、指摘と計画に記載する正確な目標値。Emil Kowalski のデザインエンジニアリング哲学（[emilkowal.ski](https://emilkowal.ski/)）を基にしている。ここにある値は近似せず、そのまま転記する。

## 1. 目的と頻度

すべてのアニメーションは「なぜ animate するのか」に答えられなければならない。空間的一貫性、state の表示、feedback、説明、急な変化の防止などが目的になる。「見栄えが良い」は、頻繁に見る要素の目的にはならない。

| Frequency | Decision |
| --- | --- |
| 1日100回以上（keyboard shortcut、command palette toggle） | animation させない。例外なし。 |
| 1日数十回（hover effect、list navigation） | 削除するか大幅に減らす |
| 時々（modal、drawer、toast） | 標準的な animation |
| まれ / 初回（onboarding、feedback、celebration） | delight を追加可能 |

探すもの: keyboard から開始される action の animation、開閉 transition のある command palette（Raycast にはなく、それが正しい）、常に操作する list item や hover state の装飾 motion。最も強い修正が、**animation の削除**であることは多い。

## 2. Easing と duration

Easing の判断順序:

- 入場または退場 → **`ease-out`**（速く始まり、responsive に感じる）
- 画面上の移動 / morphing → **`ease-in-out`**
- Hover / color change → **`ease`**
- 一定の motion（marquee、progress）→ **`linear`**
- 既定 → **`ease-out`**

UI の **`ease-in` は常に指摘対象**である。ユーザーが見ているまさにその瞬間を、遅い開始によって遅延させる。CSS 組み込みの easing は意図のある motion には弱すぎる。計画では、リポジトリの規約に合わせて、強い custom curve を token として導入する。

```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);        /* strong ease-out for UI */
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);    /* strong ease-in-out for on-screen movement */
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);     /* iOS-like drawer curve */
```

Duration budget — **UI animation は 300ms 未満に収める**。

| Element | Duration |
| --- | --- |
| Button press feedback | 100–160ms |
| Tooltip、小さな popover | 125–200ms |
| Dropdown、select | 150–250ms |
| Modal、drawer | 200–500ms |
| Marketing / explanatory | より長くてもよい |

探すもの: あらゆる `ease-in`、entrance に使われた素の `ease` / `linear`、UI element の 300ms を超える duration、toolbar 内のすべての tooltip に毎回かかる tooltip delay + animation（最初の後は即座に表示すべき）。

## 3. 物理性と origin

- **`scale(0)` は使わない**。現実世界では無から物体は現れない。目標: `scale(0.9–0.97)` + `opacity: 0`。
- **Popover / dropdown / tooltip は中央ではなく trigger を起点に scale する**。
  ```css
  .popover { transform-origin: var(--radix-popover-content-transform-origin); } /* Radix */
  .popover { transform-origin: var(--transform-origin); }                       /* Base UI */
  ```
  **Modal は例外**である。中央に現れるので、`transform-origin: center` が正しい。指摘しない。
- **Press feedback**: `:active` で `transform: scale(0.97)`、`transition: transform 160ms ease-out`。控えめにする（0.95–0.98）。

探すもの: `scale(0)`、initial transform のない純粋な fade entrance、trigger に固定された element の `transform-origin: center` または origin 指定なし、press feedback のない pressable element。

## 4. 中断可能性

CSS **transition** は animation 中に現在の state から新しい target へ切り替わる。**keyframe** はゼロから再開する。頻繁に発火するものや、motion の途中で反転できるもの（toast stack、toggle、drag、expand / collapse）は transition または spring を使う必要がある。

- JS なしの entry: `@starting-style`（legacy fallback: `useEffect` で設定する `data-mounted` attribute）。
- Gesture-driven motion には spring を使う。中断時に velocity を引き継げる。
- Apple-style の推奨 spring config: `{ type: "spring", duration: 0.5, bounce: 0.2 }`。Bounce は控えめ（0.1–0.3）にし、目に見える bounce は drag-to-dismiss と遊び心のある場面に限定する。
- **非対称 timing**: 意図のある phase（press、hold、destructive confirm）はゆっくり animate し、system response は素早く切り替える。press と release の対称 timing は指摘対象である。

探すもの: toast / toggle / 高頻度 UI の `@keyframes`、固定 duration の keyframe で tween する gesture handler、velocity に基づく dismissal のない drag（distance threshold だけでなく `Math.abs(distance)/elapsedMs > ~0.11` で dismiss）、drag boundary で増大する friction がなく急停止するもの。

## 5. Performance

- **`transform` と `opacity` だけを animate する。** `width` / `height` / `margin` / `padding` / `top` / `left` は layout + paint + composite を引き起こす。
- **`transition: all`** は意図しない property を GPU 外で animate するため、常に指摘対象である。
- **Framer Motion の `x` / `y` / `scale` shorthand は hardware-accelerated ではない**。main thread で動作し、高負荷時に frame drop を起こす。目標は完全な transform string、`animate={{ transform: "translateX(100px)" }}`。
- **親の CSS variable で子の transform を駆動しない。** すべての子で style 再計算が発生する。element に `transform` を直接設定する。
- 高負荷時は CSS（および WAAPI）が rAF-based JS より優れる。事前に決まった motion には CSS、dynamic / gesture-driven motion には JS / spring を使う。
- Transition 中の `filter: blur()` は 20px 未満にする。大きな blur は、特に Safari で高コストになる。

探すもの: `transition: all`、animate される layout property、多忙な page 上の Framer Motion shorthand prop、子の transform を駆動する `setProperty('--x', …)`、CSS で実現できる処理を行う rAF loop。

## 6. Accessibility

```css
@media (prefers-reduced-motion: reduce) {
  .element { animation: fade 0.2s ease; } /* keep opacity/color, drop movement */
}
@media (hover: hover) and (pointer: fine) {
  .element:hover { transform: scale(1.05); } /* touch fires false hovers on tap */
}
```

Reduced motion は animation をゼロにするのではなく、少なく穏やかにする。理解を助ける transition は残し、位置の変化を取り除く。JS では `useReducedMotion()` を使い、transform value を分岐する。

探すもの: `prefers-reduced-motion` 対応のない movement、条件なしの `:hover` motion、すべての feedback を消す reduced-motion 実装。

## 7. 統一感と token

- Motion は製品の個性に合わせる。遊び心があれば bounce を強められるが、dashboard は引き締める。component 間で個性が一致しない場合は指摘対象である。
- Curve と duration は shared token に置く。ほぼ同じ cubic-bezier が5つ手書きされていれば統合対象である。
- 全要素が同時に入場する group で、**30–80ms stagger** が適する場合がある。Stagger は装飾であり、interaction を妨げてはならない。
- 2つの state が重なって見える不自然な crossfade は、transition 中の控えめな `filter: blur(2px)` で隠せる。

探すもの: ほぼ同じ easing / duration の重複、引き締まったアプリ内の一つだけ bouncy な component、stagger のない list / grid entrance、二重露出が見える crossfade。

## 8. 見逃されている機会

追加に関するカテゴリ。animate していないが、すべき場所を探す。

- 急な変化を防ぐ短い transition が必要な、teleport する state change（content swap、layout jump）。
- 出所を説明する motion のない、空間的につながった UI（trigger から現れる panel）。
- 許容される delight budget を使っていない、まれで感情的価値の高い moment（first-run、success、celebration）。
- これらに使える `translate` percentage（`translateY(100%)` = element 自身の height）と `clip-path: inset()` reveal。hardcoded pixel offset は使わない。

観察した実際の UX の継ぎ目に基づくものだけを、数件まで報告する。wishlist にしない。
