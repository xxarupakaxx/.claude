# コアクラフト原則 詳細

## 4pxグリッドシステム

```css
--space-1: 4px;   /* マイクロ（アイコンギャップ） */
--space-2: 8px;   /* タイト（コンポーネント内） */
--space-3: 12px;  /* 標準（関連要素間） */
--space-4: 16px;  /* 快適（セクションパディング） */
--space-6: 24px;  /* 広め（セクション間） */
--space-8: 32px;  /* 大きな区切り */
--space-12: 48px; /* メジャーセパレーション */
```

## 対称パディング

TLBRは一致させる。非対称パディングは禁止:

```css
/* Good */
padding: 16px;
padding: 12px 16px; /* 水平にだけ余分が必要な場合のみ */

/* Bad */
padding: 24px 16px 12px 16px;
```

## ボーダーラジアス一貫性

4pxグリッドに従い、1つのシステムを選択。**混在させない:**

| Sharp | Soft | Minimal |
|-------|------|---------|
| sm: 4px | sm: 8px | sm: 2px |
| md: 6px | md: 12px | md: 4px |
| lg: 8px | lg: 16px | lg: 6px |

## コントラスト階層（4レベルシステム）

```css
--text-primary: #0f172a;   /* フォアグラウンド */
--text-secondary: #475569; /* セカンダリ */
--text-muted: #94a3b8;     /* ミュート */
--text-faint: #cbd5e1;     /* フェイント */
```

## データ表示

```css
.data-value {
  font-family: 'JetBrains Mono', monospace;
  font-variant-numeric: tabular-nums;
}
```
