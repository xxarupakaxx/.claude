# アクセシビリティ詳細ガイド（WCAG 2.1 AA）

## 色コントラスト

### 最低比率
| 要素 | 比率 | 例 |
|------|------|-----|
| 通常テキスト（< 18px） | 4.5:1 | `#475569` on `#ffffff` = 7.1:1 |
| 大テキスト（>= 18px bold / >= 24px） | 3:1 | |
| UI要素・グラフィック | 3:1 | ボタン境界、アイコン |

### チェック方法
- Chrome DevTools > Elements > Styles > Contrast ratio
- Figma: Stark プラグイン
- CLI: `npx @axe-core/cli <url>`

---

## キーボードナビゲーション

### 必須キーバインド
| キー | 動作 |
|------|------|
| `Tab` | 次のフォーカス可能要素へ |
| `Shift + Tab` | 前のフォーカス可能要素へ |
| `Enter` / `Space` | アクティベート |
| `Escape` | モーダル・ドロップダウンを閉じる |
| `Arrow Keys` | リスト・タブ・メニュー内の移動 |

### フォーカス表示
```css
/* ブラウザデフォルトを上書き */
:focus-visible {
  outline: 2px solid var(--color-info);
  outline-offset: 2px;
}

/* マウスクリック時はフォーカスリングを非表示 */
:focus:not(:focus-visible) {
  outline: none;
}
```

### フォーカストラップ（モーダル）
モーダル内のTabキーはモーダル内で循環させる。外部にフォーカスが漏れないようにする。

---

## セマンティックHTML

### ランドマーク
```html
<header role="banner">      <!-- サイトヘッダー -->
<nav role="navigation">       <!-- ナビゲーション -->
<main role="main">            <!-- メインコンテンツ -->
<aside role="complementary">  <!-- サイドバー -->
<footer role="contentinfo">   <!-- フッター -->
```

### 見出し階層
- `h1` はページに1つだけ
- 階層をスキップしない（h1 → h3 は不可、h1 → h2 → h3）
- 見出しは視覚的なサイズではなく、論理的な構造で選ぶ

---

## ARIA属性

### よく使うパターン
```html
<!-- ボタンにラベル -->
<button aria-label="メニューを開く">
  <IconMenu />
</button>

<!-- ライブリージョン（動的更新の通知） -->
<div aria-live="polite" aria-atomic="true">
  3件の新しいメッセージ
</div>

<!-- ローディング状態 -->
<div aria-busy="true" aria-live="polite">
  読み込み中...
</div>

<!-- エラーメッセージとフォーム連携 -->
<input aria-invalid="true" aria-describedby="email-error" />
<span id="email-error" role="alert">有効なメールアドレスを入力してください</span>
```

### 避けるべきこと
- `role="button"` を `<div>` に付けるより `<button>` を使う
- `aria-hidden="true"` をフォーカス可能要素に付けない
- 冗長なaria（`<button aria-label="ボタン">` は不要）

---

## Touch Target

### 最小サイズ
- **44×44px** — WCAG 2.1 AAの最小タッチターゲット
- ボタン、リンク、フォーム要素すべてに適用

```css
.touch-target {
  min-height: 44px;
  min-width: 44px;
  /* パディングで視覚的サイズを調整 */
  padding: 8px 16px;
}
```

### 間隔
- タッチターゲット間は最低 **8px** のスペース

---

## 減モーション対応

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

## 高コントラストモード

```css
@media (prefers-contrast: high) {
  :root {
    --border: rgba(0, 0, 0, 0.3);
    --text-muted: #334155;
  }
}
```

---

## テストツール

| ツール | 用途 |
|--------|------|
| axe DevTools（Chrome拡張） | 自動アクセシビリティチェック |
| WAVE | Web Accessibility Evaluation |
| Lighthouse（Chrome DevTools） | パフォーマンス + アクセシビリティ |
| VoiceOver（macOS） | スクリーンリーダーテスト |
| `npx @axe-core/cli` | CI/CDでの自動テスト |
