# モーション & アニメーション

## 基本原則

```css
/* 標準イージング */
--ease-out: cubic-bezier(0.25, 1, 0.5, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);

/* デュレーション */
--duration-fast: 150ms;   /* マイクロインタラクション */
--duration-normal: 200ms; /* 通常のトランジション */
--duration-slow: 300ms;   /* 大きなトランジション */
```

## 推奨パターン

### ホバー状態
```css
.card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-layered);
  transition: all var(--duration-fast) var(--ease-out);
}
```

### ページロードのスタッガード表示
```css
.fade-in-stagger {
  opacity: 0;
  transform: translateY(10px);
  animation: fadeIn var(--duration-normal) var(--ease-out) forwards;
}
.fade-in-stagger:nth-child(1) { animation-delay: 0ms; }
.fade-in-stagger:nth-child(2) { animation-delay: 50ms; }
.fade-in-stagger:nth-child(3) { animation-delay: 100ms; }

@keyframes fadeIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### ボタンフィードバック
```css
.button:active {
  transform: scale(0.97);
  transition: transform var(--duration-fast) var(--ease-out);
}
```

### ローディングスピナー
```css
@keyframes spin {
  to { transform: rotate(360deg); }
}
.spinner {
  animation: spin 1s linear infinite;
}
```

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

## 禁止事項

- エンタープライズUIでのスプリング / バウンシーエフェクト
- 300msを超えるトランジション（ユーザーの待ち時間増加）
- 意味のないアニメーション（装飾目的のみ）
- ページ内の過剰なアニメーション同時実行
