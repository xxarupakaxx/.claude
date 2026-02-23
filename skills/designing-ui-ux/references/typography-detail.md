# タイポグラフィ詳細

## 推奨フォントペアリング

```css
/* Modern SaaS */
--font-display: 'Geist', sans-serif;
--font-body: 'Inter', sans-serif;

/* Premium Product */
--font-display: 'Fraunces', serif;
--font-body: 'Plus Jakarta Sans', sans-serif;

/* Developer Tool */
--font-display: 'JetBrains Mono', monospace;
--font-body: 'Inter', sans-serif;

/* Editorial */
--font-display: 'Playfair Display', serif;
--font-body: 'Source Serif Pro', serif;
```

## タイポグラフィ階層

```css
/* ウェイトと詳細 */
.headline {
  font-weight: 600;
  letter-spacing: -0.02em;
}

.body {
  font-weight: 400;
  letter-spacing: 0;
}

.label {
  font-weight: 500;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  font-size: var(--text-xs);
}

/* データ用モノスペース */
.data-value {
  font-family: 'JetBrains Mono', monospace;
  font-variant-numeric: tabular-nums;
}
```

## Fluid Typography（レスポンシブ）

```css
/* clamp(min, preferred, max) */
--text-fluid-sm: clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);
--text-fluid-base: clamp(0.875rem, 0.8rem + 0.35vw, 1rem);
--text-fluid-lg: clamp(1rem, 0.9rem + 0.5vw, 1.25rem);
--text-fluid-xl: clamp(1.25rem, 1rem + 1vw, 1.75rem);
--text-fluid-2xl: clamp(1.5rem, 1.2rem + 1.5vw, 2.25rem);
--text-fluid-3xl: clamp(2rem, 1.5rem + 2.5vw, 3rem);
```

## 行間（line-height）

```css
/* 見出し — タイトに */
--leading-tight: 1.15;
--leading-snug: 1.25;

/* 本文 — 読みやすく */
--leading-normal: 1.5;
--leading-relaxed: 1.625;
```

---

## タイポグラフィスケール（基本定義）

```css
--text-xs: 11px;  --text-sm: 12px;  --text-base: 14px;
--text-lg: 16px;  --text-xl: 18px;  --text-2xl: 24px;
--text-3xl: 32px; --text-4xl: 48px;
```
