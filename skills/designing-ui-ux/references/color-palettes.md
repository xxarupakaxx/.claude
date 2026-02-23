# 業界別カラーパレット

## SaaS
```
Primary: #4F46E5 (Indigo)
Accent:  #10B981 (Emerald)
```

## Fintech
```
Primary: #0F172A (Slate)
Accent:  #22C55E (Green)
```

## Healthcare
```
Primary: #0EA5E9 (Sky)
Accent:  #14B8A6 (Teal)
```

## E-commerce
```
Primary: #7C3AED (Violet)
Accent:  #F59E0B (Amber)
```

## Creative
```
Primary: #EC4899 (Pink)
Accent:  #8B5CF6 (Purple)
```

## Developer Tools
```
Primary: #18181B (Zinc)
Accent:  #3B82F6 (Blue)
```

---

## ライト vs ダーク

- **Dark Mode** — 技術的、集中、プレミアム感
- **Light Mode** — オープン、親しみやすい、クリーン

## セマンティックカラー（ダークモード調整）

```css
/* Light Mode */
--color-success: #22c55e;
--color-warning: #f59e0b;
--color-error: #ef4444;

/* Dark Mode（彩度を下げ、明度を上げる） */
--color-success: #4ade80;
--color-warning: #fbbf24;
--color-error: #f87171;
```

## 避けるべきカラーパターン

- 汎用 `#3B82F6` ブルーのデフォルト依存
- 紫グラデーション + 白背景（AIっぽい）
- Teal-Coral コンボ（過度に使用済み）
- 無意味な装飾グラデーション
