# アニメーション基準リファレンス

レビューで用いる正確な値、曲線、規則をまとめる。
指摘では近似せず、このリファレンスの値を引用する。
Emil Kowalskiのデザインエンジニアリング思想から抽出した基準である。

## アニメーションさせるべきか（頻度表）

| 頻度 | 判断 |
| --- | --- |
| 1日100回以上（keyboard shortcuts、command palette toggle） | アニメーションさせない。例外はない |
| 1日数十回（hover効果、list navigation） | 削除するか、大幅に減らす |
| ときどき（modals、drawers、toasts） | 標準的なアニメーション |
| まれ、または初回（onboarding、feedback、celebrations） | 楽しさを加えてよい |

**キーボード起点の操作をアニメーションさせてはならない。**
1日に数百回繰り返されるため、アニメーションがあると遅く、操作と反応が分断されているように感じる。
Raycastにはopenまたはcloseのアニメーションがない。
1日に数百回使う機能として適切である。

モーションの有効な目的は、空間的な一貫性、状態の表示、説明、フィードバック、唐突な変化の防止である。
頻繁に表示される要素を「格好よく見せる」ことは、有効な目的ではない。

## イージング

次の順序で判断する。

- 登場または退場 → **`ease-out`**（速く始まり、反応がよく感じられる）
- 画面内の移動またはmorphing → **`ease-in-out`**
- hoverまたは色の変更 → **`ease`**
- 一定の動き（marquee、progress） → **`linear`**
- 既定値 → **`ease-out`**

**UIで`ease-in`を使ってはならない。**
遅く始まり、ユーザーが注視している瞬間を遅らせる。
200msの`ease-out`は、同じ200msの`ease-in`よりも速く感じられる。

CSS組み込みのイージングは弱すぎる。
強いカスタム曲線を使う。

```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);        /* strong ease-out for UI */
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);    /* strong ease-in-out for on-screen movement */
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);     /* iOS-like drawer curve (Ionic) */
```

曲線は[easing.dev](https://easing.dev/)または[easings.co](https://easings.co/)で探し、ゼロから手作りしない。

## 時間

| 要素 | 時間 |
| --- | --- |
| Button press feedback | 100–160ms |
| Tooltips、small popovers | 125–200ms |
| Dropdowns、selects | 150–250ms |
| Modals、drawers | 200–500ms |
| Marketingまたはexplanatory | 長くてもよい |

**規則：UIアニメーションは300ms未満に収める。**
180msのdropdownは400msのものより反応がよく感じられる。
spinnerを速くすると、実際の時間が同じでも読み込みが速く感じられる。
2回目以降のtooltipを即座に表示し、遅延とアニメーションを省くと、toolbarの反応が速く感じられる。

## 物理的な自然さ

- **`scale(0)`を使ってはならない。** `scale(0.9–0.97)`と`opacity: 0`から始める。現実の物体が無から現れることはない。
- **起点を考慮したpopovers。** 中央ではなくトリガーを起点に拡大する。
  ```css
  .popover { transform-origin: var(--radix-popover-content-transform-origin); } /* Radix */
  .popover { transform-origin: var(--transform-origin); }                       /* Base UI */
  ```
  **Modalsは例外である。**
  viewportの中央に現れるため、`transform-origin: center`を維持する。
- **Button press feedback。** `:active`で`transform: scale(0.97)`を指定し、`transition: transform 160ms ease-out`を使う。0.95–0.98の範囲で控えめにする。押せるすべての要素に適用できる。

## Springs

物理現象を再現するため、自然に感じられる。
固定された時間はなく、parametersによって収束する。
momentumを伴うdrag、「生きている」要素（Dynamic Island）、中断可能なgestures、装飾的なmouse-trackingに使う。

```js
// Apple-style (easier to reason about) — recommended
{ type: "spring", duration: 0.5, bounce: 0.2 }

// Traditional physics (more control)
{ type: "spring", mass: 1, stiffness: 100, damping: 10 }
```

bounceは0.1–0.3の範囲で控えめにする。
ほとんどのUIではbounceを避け、drag-to-dismissと遊び心のあるinteractionに限る。
Springsは中断時のvelocityを維持するが、keyframesはゼロから再開する。
そのため、ユーザーが途中で方向を反転できるgesturesに適する。

mouse interactionsでは、値をmouse positionへ直接結び付けず、`useSpring`で補間する。
直接結び付けると人工的に見え、momentumも生まれない。
装飾的なモーションである場合に限って使う。

## 中断可能性

CSSの**transitions**はアニメーションの途中で中断し、対象を変更できる。
**keyframes**はゼロから再開する。
toastの追加やtoggleなど、短時間で繰り返し発火するものにはtransitionsのほうが滑らかである。

```css
/* Interruptible — good for dynamic UI */
.toast { transition: transform 400ms ease; }

/* Not interruptible — avoid for dynamic UI */
@keyframes slideIn { from { transform: translateY(100%); } to { transform: translateY(0); } }
```

JSを使わずに登場させる場合は、`@starting-style`を使う。

```css
.toast {
  opacity: 1; transform: translateY(0);
  transition: opacity 400ms ease, transform 400ms ease;
  @starting-style { opacity: 0; transform: translateY(100%); }
}
```

旧環境向けのfallbackには、`useEffect(() => setMounted(true), [])`と`data-mounted`属性を使う。

## 非対称な時間

ユーザーが判断している間は遅くし、システムが応答する場面は速くする。

```css
.overlay { transition: clip-path 200ms ease-out; }            /* release: fast */
.button:active .overlay { transition: clip-path 2s linear; }  /* press: slow, deliberate */
```

## パフォーマンス

- **アニメーションの対象は`transform`と`opacity`だけにする。** layoutとpaintを回避し、GPUで動作する。`padding`、`margin`、`height`、`width`、`top`、`left`は3つのrendering stepsをすべて発生させる。
- **親要素のCSS変数で子要素のtransformsを駆動しない。** すべての子要素でstylesが再計算される。対象要素の`transform`を直接設定する。
  ```js
  element.style.setProperty('--swipe-amount', `${d}px`); // bad: recalc on all children
  element.style.transform = `translateY(${d}px)`;        // good: only this element
  ```
- **Framer Motionの短縮記法はhardware-acceleratedではない。** `x`、`y`、`scale`はrAFによってmain threadで動作し、高負荷時にフレーム落ちする。完全なtransform文字列を使う。
  ```jsx
  <motion.div animate={{ x: 100 }} />                          // drops frames under load
  <motion.div animate={{ transform: "translateX(100px)" }} />  // hardware accelerated
  ```
- **高負荷時はCSS animationsがJSより優れる。** main thread外で動作する。rAFベースのanimationsは、browserがload、script、paintを処理している間に引っかかる。事前に決まったモーションにはCSSを使い、動的または中断可能なものにはJSを使う。
- **WAAPI**はCSSと同等のパフォーマンスをJSから制御できる。hardware-acceleratedで中断可能であり、libraryも不要である。
  ```js
  element.animate([{ clipPath: 'inset(0 0 100% 0)' }, { clipPath: 'inset(0 0 0 0)' }],
    { duration: 1000, fill: 'forwards', easing: 'cubic-bezier(0.77, 0, 0.175, 1)' });
  ```

## Transformsとclip-path

- **`translate`のpercentage**は要素自身の大きさを基準にする。`translateY(100%)`は要素の寸法にかかわらず、その要素のheight分だけ移動する。SonnerとVaulはこの方法でtoastsとdrawersを配置している。hardcoded pxより優先する。
- **`scale()`は子要素も拡大縮小する。** font、icons、contentも対象になる。press feedbackでは、この性質を利用する。
- **3D：** `rotateX/Y`と`transform-style: preserve-3d`を使うと、JSなしでdepth、orbit、flipを表現できる。
- **`clip-path: inset(t r b l)`**は強力なアニメーション手段である。各値は対応する辺から内側を切り取る。reveal-on-scroll（`inset(0 0 100% 0)`から`inset(0 0 0 0)`）、hold-to-delete overlay、継ぎ目のないtab color transitions（active copyを複製してclipする）、comparison slidersに使える。

## Gesturesとdrag

- **Momentum dismissal：** 距離のthresholdを越えることだけを条件にしない。velocity（`Math.abs(distance)/elapsedMs`）を計算し、`> ~0.11`ならdismissする。flickだけで十分にする。
- **境界でのdamping：** 自然な境界を越えてdragすると、進むほど移動量を小さくする。現実の物体が停止前に減速する動きに合わせる。
- drag開始時に**pointer capture**し、pointerが範囲外へ出ても継続させる。
- **Multi-touch protection：** drag開始後の追加touch pointsを無視する（`if (isDragging) return`）。位置の跳躍を防ぐ。
- **hard stopsよりfrictionを使う。** 見えない壁で止めず、抵抗を増やしながらover-dragを許可する。

## 不完全なcrossfadeを隠す

easingとdurationを調整してもcrossfadeで2つの状態が重なって見える場合は、transition中に控えめな`filter: blur(2px)`を加え、知覚上の一つの変形に見せる。
blurは20px未満にする。
特にSafariでは、強いblurの処理負荷が高い。

## Stagger

グループの登場にはstaggerを使い、各要素の間隔を30–80msにする。
これより長い遅延は鈍く感じられる。
staggerは装飾であり、再生中にinteractionを妨げてはならない。

```css
.item { opacity: 0; transform: translateY(8px); animation: fadeIn 300ms ease-out forwards; }
.item:nth-child(2) { animation-delay: 50ms; }
.item:nth-child(3) { animation-delay: 100ms; }
@keyframes fadeIn { to { opacity: 1; transform: translateY(0); } }
```

## アクセシビリティ

```css
@media (prefers-reduced-motion: reduce) {
  .element { animation: fade 0.2s ease; } /* keep opacity/color, drop transform-based motion */
}
@media (hover: hover) and (pointer: fine) {
  .element:hover { transform: scale(1.05); } /* gate hover motion — touch fires false hovers on tap */
}
```

```jsx
const reduce = useReducedMotion();
const closedX = reduce ? 0 : '-100%';
```

Reduced motionは、アニメーションをゼロにするのではなく、少なく穏やかにすることを意味する。
理解を助けるtransitionsは残し、移動または位置の変化をなくす。

## デバッグ（感触を判断できないレビューで推奨）

- **Slow motion：** durationを2–5倍にするか、DevTools animation inspectorを使う。colorsが滑らかにcrossfadeするか、easingが唐突に停止しないか、`transform-origin`が正しいか、連動するpropertiesの同期が保たれているかを確認する。
- **Frame-by-frame：** Chrome DevTools Animations panelを使うと、連動するproperties間のtiming driftがわかる。
- gestures（drawers、swipe）は**実機**で確認する。phoneを接続し、IP経由でdev serverへアクセスし、Safari remote devtoolsを使う。
- **翌日に新鮮な目で見る。** 開発中には見えなかった不備が、時間を置くと見つかる。

## 統一感

モーションをコンポーネントの性格に合わせる。
遊び心のあるコンポーネントはbounceを強めてもよいが、業務用dashboardはきびきびと速く動かす。
Sonnerの感触が適切なのは、easing、duration、design、名前までが調和していることも理由である。
優雅に感じられるよう、やや遅くし、`ease-out`ではなく`ease`を使っている。
listのenterとexitでopacityとheightを組み合わせる方法は試行錯誤が必要であり、公式は存在しない。
感触が適切になるまで調整する。
