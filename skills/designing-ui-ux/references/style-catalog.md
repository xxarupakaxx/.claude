# UIスタイルカタログ

## 深度戦略（CSS実装）

### Option A: Borders-only（フラット）
```css
--border: rgba(0, 0, 0, 0.08);
--border-subtle: rgba(0, 0, 0, 0.05);
border: 0.5px solid var(--border);
```
→ クリーン、技術的、密度重視（Linear, Raycast）

### Option B: Single Shadow（シンプル）
```css
--shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
```
→ ソフトリフト、親しみやすい

### Option C: Layered Shadows（リッチ）
```css
--shadow-layered:
  0 0 0 0.5px rgba(0, 0, 0, 0.05),
  0 1px 2px rgba(0, 0, 0, 0.04),
  0 2px 4px rgba(0, 0, 0, 0.03),
  0 4px 8px rgba(0, 0, 0, 0.02);
```
→ プレミアム、立体感（Stripe, Mercury）

### Option D: Surface Color Shifts
```css
--surface-0: #ffffff;
--surface-1: #f8fafc;
--surface-2: #f1f5f9;
```
→ 影なしで色相による階層

---

## ビジュアルスタイル

### Glassmorphism
```css
.glass-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 16px;
}
```
**注意: 控えめに使用。メインUIには不向き。**

### Neumorphism
```css
.neu-card {
  background: #e0e5ec;
  box-shadow:
    8px 8px 16px #a3b1c6,
    -8px -8px 16px #ffffff;
  border-radius: 20px;
}
```

### Claymorphism
```css
.clay-card {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-radius: 24px;
  box-shadow:
    inset 2px 2px 4px rgba(255, 255, 255, 0.5),
    8px 8px 16px rgba(0, 0, 0, 0.1);
}
```

### Bento Grid
```css
.bento-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.bento-card-large {
  grid-column: span 2;
  grid-row: span 2;
}
```

### Dark Mode Premium
```css
.dark-premium {
  background: #0a0a0a;
  color: #fafafa;
  --accent: #3b82f6;
  --border: rgba(255, 255, 255, 0.08);
}
```

---

## ダークモード考慮事項

### 影より境界線
ダーク背景では影が見えにくい。境界線で定義:
```css
.dark-mode .card {
  background: #1a1a1a;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: none;
}
```

### サイドバー設計
メインコンテンツと同じ背景、微妙なボーダーで分離:
```css
.sidebar {
  background: var(--surface-0);
  border-right: 1px solid var(--border);
  width: 240px;
}
```
