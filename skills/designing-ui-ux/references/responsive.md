# レスポンシブ設計詳細

## ブレークポイントシステム

```css
/* Mobile First: min-widthで拡張 */
/* Base: 0-639px (モバイル) */
@media (min-width: 640px)  { /* sm: モバイル横 */ }
@media (min-width: 768px)  { /* md: タブレット */ }
@media (min-width: 1024px) { /* lg: デスクトップ */ }
@media (min-width: 1280px) { /* xl: ワイド */ }
@media (min-width: 1536px) { /* 2xl: ウルトラワイド */ }
```

## Tailwind ブレークポイント対応

```css
/* Tailwindのデフォルト */
sm: 640px
md: 768px
lg: 1024px
xl: 1280px
2xl: 1536px
```

---

## レイアウトパターン

### サイドバー + メインコンテンツ

```css
/* モバイル: サイドバー非表示 */
.layout {
  display: grid;
  grid-template-columns: 1fr;
}

/* デスクトップ: サイドバー表示 */
@media (min-width: 1024px) {
  .layout {
    grid-template-columns: 240px 1fr;
  }
}
```

### カードグリッド

```css
.card-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: 1fr; /* モバイル: 1列 */
}

@media (min-width: 640px) {
  .card-grid {
    grid-template-columns: repeat(2, 1fr); /* タブレット: 2列 */
  }
}

@media (min-width: 1024px) {
  .card-grid {
    grid-template-columns: repeat(3, 1fr); /* デスクトップ: 3列 */
  }
}
```

### Bento Grid（レスポンシブ）

```css
.bento-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: 1fr; /* モバイル */
}

@media (min-width: 768px) {
  .bento-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .bento-large {
    grid-column: span 2;
  }
}

@media (min-width: 1024px) {
  .bento-grid {
    grid-template-columns: repeat(4, 1fr);
  }
  .bento-large {
    grid-column: span 2;
    grid-row: span 2;
  }
}
```

---

## Fluid Typography

```css
/* clamp(最小値, 推奨値, 最大値) */
h1 { font-size: clamp(1.75rem, 1.5rem + 2vw, 3rem); }
h2 { font-size: clamp(1.25rem, 1rem + 1.5vw, 2.25rem); }
h3 { font-size: clamp(1.125rem, 1rem + 0.5vw, 1.5rem); }
body { font-size: clamp(0.875rem, 0.8rem + 0.35vw, 1rem); }
```

---

## Container Queries（モダン）

```css
/* コンテナ定義 */
.card-container {
  container-type: inline-size;
  container-name: card;
}

/* コンテナサイズに応じたスタイル */
@container card (min-width: 400px) {
  .card-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
}
```

---

## タッチ最適化

```css
/* タッチデバイスでのホバー無効化 */
@media (hover: none) {
  .card:hover {
    transform: none;
    box-shadow: var(--shadow); /* ホバーエフェクトなし */
  }
}

/* タッチターゲット最小サイズ */
.touch-target {
  min-height: 44px;
  min-width: 44px;
}

/* タッチターゲット間のスペース */
.nav-item + .nav-item {
  margin-top: 8px;
}
```

---

## テーブルのレスポンシブ対応

### 横スクロール方式
```css
.table-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
```

### カード変換方式（モバイル）
```css
@media (max-width: 767px) {
  table, thead, tbody, th, td, tr {
    display: block;
  }
  thead { display: none; }
  td {
    position: relative;
    padding-left: 50%;
  }
  td::before {
    content: attr(data-label);
    position: absolute;
    left: 12px;
    font-weight: 600;
  }
}
```

---

## 画像のレスポンシブ対応

```css
img {
  max-width: 100%;
  height: auto;
}
```

```html
<!-- srcset + sizes で最適な画像を配信 -->
<img
  srcset="image-400.webp 400w, image-800.webp 800w, image-1200.webp 1200w"
  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
  src="image-800.webp"
  alt="説明文"
  loading="lazy"
/>
```
