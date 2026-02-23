---
name: designing-ui-ux
description: |
  プロダクショングレードのUI/UXを設計・実装する統合デザインスキル。
  ダッシュボード、管理画面、LP、Webアプリケーション等のUI構築時に使用。
  Linear/Notion/Stripe/Vercel品質を再現し、AIっぽい平凡なデザインを回避。
  デザインメモリでセッション横断の一貫性を保証。WCAG 2.1 AA準拠。
  使用タイミング: (1) UIコンポーネント構築、(2) デザイン改善・リデザイン、(3) ダッシュボード・管理画面設計。
  「UIを作って」「デザインを改善して」「ダッシュボードを設計して」「レスポンシブ対応して」「アクセシビリティを改善して」等の依頼に対応。
  対象: .tsx, .css, .scss, tailwind.config ファイル。
---

# UI/UX Design Skill

プロダクション品質のUIを設計・実装するための統合スキル。
AIの「distributional convergence」（Inter + 紫グラデーション + 最小限アニメーション = "AI slop"）を克服し、コンテキスト駆動の独自デザインを生成する。

---

## Phase 0: デザインメモリ

セッション開始時、PJルートの `.interface-design/system.md` を確認する。

### system.md が存在する場合

1. ファイルを読み込み、確立済みの Direction / Tokens / Patterns を適用
2. 新しいパターンが生まれたら追記を提案

### system.md が存在しない場合

1. Phase 1-2 でデザイン基盤を確立
2. セッション終了時に `.interface-design/system.md` への保存を提案

### system.md フォーマット

```markdown
# Design System

## Direction
- Personality: [e.g., Precision & Density]
- Foundation: [e.g., Cool (slate, blue-gray)]
- Depth Strategy: [e.g., Borders-only]

## Tokens
- Spacing: [4px base grid values]
- Colors: [primary, accent, semantic]
- Radius: [sm, md, lg values]
- Typography: [font stack, scale]

## Patterns
- [Component]: [specific measurements]

## Decisions
- [YYYY-MM-DD]: [what and why]
```

---

## Phase 1: デザイン方向性の決定（必須）

**コードを書く前に、必ずデザイン方向性を決定する。デフォルトに頼らない。**

### コンテキスト分析（4つの問い）

1. **プロダクトの目的は？** ファイナンスとクリエイティブでは必要なエネルギーが異なる
2. **ユーザーは誰か？** パワーユーザー＝情報密度、カジュアル＝ガイダンス
3. **感情的な仕事は？** 信頼？効率？喜び？集中？
4. **何が記憶に残るか？** すべてのプロダクトに独自性を出すチャンスがある

### デザインパーソナリティ

| 方向性 | 美学 | 参考 |
|--------|------|------|
| **Precision & Density** | タイトな間隔、モノクロ、情報優先 | Linear, Raycast |
| **Warmth & Approachability** | 広い余白、柔らかい影、フレンドリー | Notion, Coda |
| **Sophistication & Trust** | クールな色調、レイヤード深度 | Stripe, Mercury |
| **Boldness & Clarity** | 高コントラスト、大胆な余白 | Vercel |
| **Utility & Function** | ミュートなパレット、機能的密度 | GitHub |
| **Data & Analysis** | チャート最適化、数字第一 | アナリティクス、BI |

**1つを選ぶか、2つをブレンドする。しかし、プロダクトに合った方向性にコミットする。**

### トーンの選択（大胆なアプローチ）

以下から選択またはインスパイア:
Brutally Minimal / Maximalist Chaos / Retro-Futuristic / Organic-Natural / Luxury-Refined / Playful-Toy / Editorial-Magazine / Brutalist-Raw / Art Deco-Geometric / Soft-Pastel / Industrial-Utilitarian

---

## Phase 2: デザイン基盤

### カラー

**ベース選択:**

| タイプ | 特徴 | 用途 |
|--------|------|------|
| **Warm** | クリーム、ウォームグレー | 親しみやすい、人間的 |
| **Cool** | スレート、ブルーグレー | プロフェッショナル、信頼性 |
| **Pure** | トゥルーグレー、黒/白 | ミニマル、大胆、技術的 |
| **Tinted** | 微妙なカラーキャスト | 独自性、ブランド |

**色は意味のためだけに使用。** グレーで構造を構築し、色はステータス・アクション・エラー・成功のみ:

```css
--color-success: #22c55e;
--color-warning: #f59e0b;
--color-error: #ef4444;
--color-info: #3b82f6;
```

**アクセントカラー** — 1つだけ選ぶ: Blue=信頼 / Green=成長 / Orange=エネルギー / Violet=創造性

→ 業界別推奨パレット詳細は `references/color-palettes.md` を参照

### タイポグラフィ

**フォントスタック選択:**

| タイプ | フォント | トーン |
|--------|----------|--------|
| **System** | -apple-system, BlinkMacSystemFont | 速い、ネイティブ |
| **Geometric Sans** | Geist, Inter, Satoshi | モダン、クリーン |
| **Humanist Sans** | SF Pro, Plus Jakarta Sans | 暖かい、親しみやすい |
| **Mono** | JetBrains Mono, Fira Code | 技術、開発者 |
| **Editorial** | Playfair Display, Fraunces | 出版物、ラグジュアリー |

**スケール:**

```css
--text-xs: 11px;  --text-sm: 12px;  --text-base: 14px;
--text-lg: 16px;  --text-xl: 18px;  --text-2xl: 24px;
--text-3xl: 32px; --text-4xl: 48px;
```

→ フォントペアリング・ウェイト詳細は `references/typography-detail.md` を参照

### 深度 & エレベーション

**1つのアプローチを選び、コミットする:**

- **A: Borders-only** — クリーン、技術的（Linear, Raycast）
- **B: Single Shadow** — ソフトリフト、親しみやすい
- **C: Layered Shadows** — プレミアム、立体感（Stripe, Mercury）
- **D: Surface Color Shifts** — 影なしで色相による階層

→ CSS実装詳細は `references/style-catalog.md` を参照

---

## Phase 3: コアクラフト原則

### 4pxグリッドシステム

```css
--space-1: 4px;   /* マイクロ（アイコンギャップ） */
--space-2: 8px;   /* タイト（コンポーネント内） */
--space-3: 12px;  /* 標準（関連要素間） */
--space-4: 16px;  /* 快適（セクションパディング） */
--space-6: 24px;  /* 広め（セクション間） */
--space-8: 32px;  /* 大きな区切り */
--space-12: 48px; /* メジャーセパレーション */
```

### 対称パディング

TLBRは一致させる。非対称パディングは禁止:

```css
/* Good */
padding: 16px;
padding: 12px 16px; /* 水平にだけ余分が必要な場合のみ */

/* Bad */
padding: 24px 16px 12px 16px;
```

### ボーダーラジアス一貫性

4pxグリッドに従い、1つのシステムを選択。**混在させない:**

| Sharp | Soft | Minimal |
|-------|------|---------|
| sm: 4px | sm: 8px | sm: 2px |
| md: 6px | md: 12px | md: 4px |
| lg: 8px | lg: 16px | lg: 6px |

### コントラスト階層（4レベルシステム）

```css
--text-primary: #0f172a;   /* フォアグラウンド */
--text-secondary: #475569; /* セカンダリ */
--text-muted: #94a3b8;     /* ミュート */
--text-faint: #cbd5e1;     /* フェイント */
```

### データ表示

```css
.data-value {
  font-family: 'JetBrains Mono', monospace;
  font-variant-numeric: tabular-nums;
}
```

---

## Phase 4: コンポーネント設計

### カードレイアウト多様性

単調なカードレイアウトは怠慢。内容に合わせて内部構造を設計:
- メトリクスカード → スパークライン
- プランカード → CTAと比較
- 設定カード → 2カラム分割
- ユーザーカード → アバタースタック

**表面処理（境界線、影、角丸、パディング、タイポグラフィ）は一貫させ、内部構造は内容に合わせる。**

### コントロール

日付ピッカー、フィルター等は洗練されたオブジェクトとして設計:

```css
.control-container {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--surface-1);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  white-space: nowrap;
}
```

**ネイティブフォーム要素をスタイル付きUIに使用しない。カスタムコンポーネントを構築する。**

### ナビゲーション

1. **ナビゲーション** — サイドバーまたはトップナビ
2. **現在地インジケーター** — パンくず、ページタイトル、アクティブ状態
3. **ユーザーコンテキスト** — ログインユーザー、ワークスペース/組織

### アイコン

推奨: **Phosphor Icons** / **Lucide** / **Heroicons**
原則: アイコンは明確化のみ。意味なく削除できるアイコンは不要。

→ UIスタイルカタログ（Glass, Neu, Clay, Bento等）は `references/style-catalog.md` を参照
→ モーション & アニメーションは `references/animation.md` を参照

---

## Phase 5: 品質ゲート（Mandate Checks）

**コードを提示する前に、4つのテストを必ず実行する:**

### Swap Test
このプロダクト名を別のブランドに置き換えても気づかれないなら、デザインが汎用的すぎる。
→ 何か1つ、このプロダクト固有の「署名」を加える

### Squint Test
画面を半目で見て、視覚的階層が読み取れるか。
→ コントラスト、サイズ、余白で明確な階層を作る

### Signature Test
このインターフェースに記憶に残る独自要素があるか。
→ ユニークなインタラクション、レイアウト、ビジュアル要素を1つ以上

### Token Test
すべてのデザイントークンがシステムに従っているか。
→ スペーシング、カラー、フォント、ラジアスの一貫性を検証

---

## Phase 6: アクセシビリティ（WCAG 2.1 AA準拠）

**アクセシビリティは非交渉的要件。オプションではない。**

### 必須チェック

- **色コントラスト**: 通常テキスト 4.5:1、大テキスト 3:1、UI要素 3:1
- **キーボード操作**: Tab / Shift+Tab / Enter / Escape / Arrow で全操作可能
- **フォーカス表示**: `:focus-visible` で明確なアウトライン（2px以上）
- **Touch target**: モバイルで最小 44×44px
- **スクリーンリーダー**: 意味のある `aria-label`、ランドマーク、見出し階層
- **減モーション対応**: `prefers-reduced-motion` メディアクエリ

→ 詳細なWCAGガイドラインは `references/accessibility.md` を参照

---

## Phase 7: レスポンシブ設計

**Mobile-first アプローチを採用する。**

### ブレークポイント

```css
--bp-sm: 640px;   /* モバイル横 */
--bp-md: 768px;   /* タブレット */
--bp-lg: 1024px;  /* デスクトップ */
--bp-xl: 1280px;  /* ワイドスクリーン */
```

### 原則

1. **モバイルファースト**: `min-width` メディアクエリで拡張
2. **Fluid Typography**: `clamp()` で滑らかなスケーリング
3. **レイアウト適応**: Grid / Flexbox で画面サイズに応じた構造変更
4. **タッチ最適化**: ボタン・リンクの十分なサイズとスペーシング

→ 詳細なブレークポイントパターンは `references/responsive.md` を参照

---

## 複数案提示（大規模変更時）

デザイン改善やリデザインでは3つのプランを提案:

| プラン | アプローチ | リスク |
|--------|-----------|--------|
| **A: Progressive** | 既存デザインの段階的改善。最小変更、低リスク | 低 |
| **B: Radical** | フレームワークを壊す大胆な再設計。野心的 | 中 |
| **C: Ideal** | リソース制約なしの理想形。長期ビジョン | 高 |

各プランにモックアップまたは詳細説明を添え、ユーザーに選択を委ねる。

---

## アンチパターン

### 絶対にやらない

- ドラマチックなドロップシャドウ（`box-shadow: 0 25px 50px...`）
- 小要素に大ボーダーラジアス（16px+）
- 理由のない非対称パディング
- 色付き背景上の純白カード
- 装飾用の太ボーダー（2px+）
- 過剰なスペーシング（セクション間48px以上）
- スプリング / バウンシーアニメーション
- 装飾的なグラデーション
- 1インターフェースに複数アクセントカラー
- **紫グラデーション + 白背景（AIっぽい）**
- **Inter, Arial, Robotoへのデフォルト依存**
- **汎用 `#3B82F6` ブルー、teal-coral コンボ**
- **Glassmorphism濫用、Apple模倣、テンプレート的レイアウト**

### 常に自問する

1. 「デフォルトに逃げていないか？」
2. 「コンテキストとユーザーに合っているか？」
3. 「深度戦略は一貫して意図的か？」
4. 「すべてがグリッド上にあるか？」
5. 「何が記憶に残るか？」

---

## 実装チェックリスト

### コーディング前
- [ ] デザインメモリ（system.md）を確認した
- [ ] デザイン方向性を決定した
- [ ] カラーファウンデーションを選択した
- [ ] タイポグラフィスタックを決定した
- [ ] 深度戦略を選択した

### コーディング中
- [ ] 4pxグリッドに従っている
- [ ] パディングが対称的
- [ ] ボーダーラジアスが一貫
- [ ] カラーは意味のためだけに使用
- [ ] データにモノスペース使用
- [ ] WCAG 2.1 AA準拠

### コーディング後
- [ ] 4つの品質ゲート（Swap / Squint / Signature / Token）通過
- [ ] レスポンシブ対応確認
- [ ] ダークモード対応確認
- [ ] キーボード操作確認
- [ ] ナビゲーションコンテキストあり
- [ ] system.md への保存を提案

---

## 技術ドキュメント参照（Context7）

| ライブラリ | Context7 Library ID | 用途 |
|-----------|---------------------|------|
| React | `/facebook/react` | コンポーネント設計 |
| Next.js | `/vercel/next.js` | ルーティング、SSR |
| Tailwind CSS | `/tailwindlabs/tailwindcss` | ユーティリティクラス |
| shadcn/ui | `/shadcn-ui/ui` | コンポーネントライブラリ |
| Radix UI | `/radix-ui/primitives` | アクセシブルなプリミティブ |
| Framer Motion | `/framer/motion` | アニメーション |

---

## 出典・マージ元

| スキル名 | 作者 | リポジトリ |
|----------|------|------------|
| frontend-design | Anthropic | https://github.com/anthropics/claude-code/tree/main/plugins/frontend-design |
| claude-design-skill | Dammyjay93 | https://github.com/Dammyjay93/claude-design-skill |
| ui-ux-pro-max-skill | nextlevelbuilder | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill |
| **interface-design** | **Dammyjay93** | **https://github.com/Dammyjay93/interface-design** |
| **bencium-claude-code-design-skill** | **bencium** | **https://github.com/bencium/bencium-claude-code-design-skill** |
| **claude-designer-skill** | **joeseesun** | **https://github.com/joeseesun/claude-designer-skill** |
| **v0 System Prompt** | **Vercel** | **https://vercel.com** |

**Remember: Claude is capable of extraordinary creative work.**
