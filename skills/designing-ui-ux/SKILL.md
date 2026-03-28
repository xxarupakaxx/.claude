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

- **存在する場合**: 読み込み、確立済みの Direction / Tokens / Patterns を適用。新パターンは追記提案。
- **存在しない場合**: Phase 1-2 で基盤確立後、保存を提案。

### system.md フォーマット

`Direction`（Personality / Foundation / Depth Strategy）、`Tokens`（Spacing / Colors / Radius / Typography）、`Patterns`（Component: measurements）、`Decisions`（日付: what and why）の4セクション構成。

---

## Phase 1: Planner（製品仕様の展開）

**短いプロンプト（1-4文）を完全な製品仕様書に展開する。**

記事 "Harness Design for Long-Running Apps" の知見: Plannerが初期段階で技術的詳細を定義しようとして誤りを犯すと、その誤りが下流の実装にまで波及する。生成すべき成果物を限定し、作業を進める中でその道筋を自ら見つけ出させる方が賢明。

### 入力

ユーザーからの短いプロンプト（1-4文）。例:
- 「プロジェクト管理ツールを作って」
- 「飲食店の予約管理ダッシュボード」
- 「開発者向けのAPIモニタリング画面」

**既に詳細な仕様がある場合**: このフェーズをスキップしてPhase 2へ

### 展開ルール

1. **スコープは野心的に**: 機能を絞らず、プロダクトとして成立する範囲まで広げる
2. **製品コンテキストに集中**: 「何を作るか」「誰が使うか」「なぜ必要か」を深掘りする
3. **技術的詳細に踏み込まない**: 実装方法・DB設計・API設計は後続Phaseに委ねる。Plannerが定義するのは「何が必要か」であり「どう作るか」ではない
4. **AI機能の機会を探す**: プロダクトにAI/自動化を組み込める箇所を提案する

### 出力: 製品仕様書

```markdown
# {プロダクト名}

## ビジョン
{1-2文。このプロダクトが存在する理由}

## ターゲットユーザー
- ペルソナ: {誰が、どんな状況で使うか}
- 主な課題: {解決する問題}

## コア機能
1. {機能名}: {機能の説明。ユーザーストーリー形式推奨}
2. ...

## 画面一覧
- {画面名}: {目的と主要な要素}
- ...

## AI/自動化の機会
- {どこにAIを組み込めるか、なぜ有効か}

## 感情的な仕事
- {このプロダクトがユーザーに提供すべき感情: 信頼/効率/喜び/安心 等}
```

### ユーザー確認

仕様書を提示し、AskUserQuestionで承認を得てからPhase 2へ進む。
ユーザーが機能を追加・削除・変更した場合は仕様書を更新。

---

## Phase 2: デザイン方向性の決定（必須）

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

## Phase 3: デザイン基盤

### カラー

| タイプ | 特徴 | 用途 |
|--------|------|------|
| **Warm** | クリーム、ウォームグレー | 親しみやすい、人間的 |
| **Cool** | スレート、ブルーグレー | プロフェッショナル、信頼性 |
| **Pure** | トゥルーグレー、黒/白 | ミニマル、大胆、技術的 |
| **Tinted** | 微妙なカラーキャスト | 独自性、ブランド |

-> セマンティックカラー・アクセント・業界別パレットは `references/color-palettes.md` を参照

### タイポグラフィ

| タイプ | フォント | トーン |
|--------|----------|--------|
| **System** | -apple-system, BlinkMacSystemFont | 速い、ネイティブ |
| **Geometric Sans** | Geist, Inter, Satoshi | モダン、クリーン |
| **Humanist Sans** | SF Pro, Plus Jakarta Sans | 暖かい、親しみやすい |
| **Mono** | JetBrains Mono, Fira Code | 技術、開発者 |
| **Editorial** | Playfair Display, Fraunces | 出版物、ラグジュアリー |

-> スケール・ペアリング・ウェイト詳細は `references/typography-detail.md` を参照

### 深度 & エレベーション

**1つのアプローチを選び、コミットする:**

- **A: Borders-only** -- クリーン、技術的（Linear, Raycast）
- **B: Single Shadow** -- ソフトリフト、親しみやすい
- **C: Layered Shadows** -- プレミアム、立体感（Stripe, Mercury）
- **D: Surface Color Shifts** -- 影なしで色相による階層

-> CSS実装詳細は `references/style-catalog.md` を参照

---

## Phase 4: コアクラフト原則

以下の原則を守る（CSS実装詳細は `references/craft-principles.md` を参照）:

1. **4pxグリッドシステム** -- すべてのスペーシングを4の倍数に
2. **対称パディング** -- TLBRは一致。非対称パディング禁止
3. **ボーダーラジアス一貫性** -- Sharp / Soft / Minimal から1つ選択、混在させない
4. **コントラスト階層** -- primary / secondary / muted / faint の4レベル
5. **データ表示** -- 数値にはモノスペース + tabular-nums

-> UIスタイルカタログ（Glass, Neu, Clay, Bento等）は `references/style-catalog.md` を参照
-> モーション & アニメーションは `references/animation.md` を参照

---

## Phase 5: コンポーネント設計

カード・コントロール・ナビゲーション・アイコンの設計原則。
表面処理は一貫させ、内部構造は内容に合わせる。ネイティブフォーム要素よりカスタムコンポーネント。

-> 詳細は `references/components.md` を参照

---

## Phase 6: 評価ループ（Generate → Evaluate → Iterate）

**生成と評価を分離し、フィードバックループでデザイン品質を引き上げる。**

記事 "Harness Design for Long-Running Apps" の核心: 生成者の自己評価より、独立した評価者による外部フィードバックの方が効果的。

### ループ構造

```
生成（Phase 2-5の実��結果）
  ↓
評価（ui-ux-reviewer サブエージェント���
  ↓ スコア + フィードバック
判定
  ├─ PASS (≥25/35) → Phase 7へ
  ├─ ITERATE (18-24) → フィードバ��クを適用して修正 → 再評価
  └─ FAIL (<18) → Phase 2に戻り方向性を再検討
```

### 評価の実行

1. **`ui-ux-reviewer`をサブエージェントとして起動**（評価ループモード）
   - 対象ファイルのフルパスを渡す
   - `.interface-design/system.md`があればパスも渡す
   - `playwright-skill`でスクリーンショット取得済みならその画像パスも渡す
2. **スコアリング結果を確認**: 4基準の加重合計（/35）
3. **フィードバックを適用**:
   - **Keep**: 触らない（良い部分を壊さない）
   - **Fix**: 指示に従い修正（ファイル・行番号・具体値が指定されている）
   - **Consider**: 余裕があれば対応

### イテレーション制御

| 設定 | 値 | 理由 |
|------|-----|------|
| 最大イテレーション | **3回** | 3回で改善が収束しなければ方向性の問題 |
| PASS閾値 | **25/35** | デザイン品質3+独自性3以上が必要 |
| 早期終了 | スコア30以上 or Fixが0件 | 十分な品質に達した場合 |

### Playwright連携（dev serverが起動可能な場合）

評価の精度を高めるため、可能であれば`playwright-skill`で実際のUIを確認する:

1. dev serverを起動
2. 変更した画面のスクリーンショットを取得
3. スクリーンショットを`ui-ux-reviewer`に渡す（画像パスをプロンプトに含める）
4. レスポンシブ確認: 3ビューポート（375px, 768px, 1440px）でキャプチャ

**Playwright連携はオプション**: dev serverが起動できない場合やコンポーネント単体の場合はコードレビューのみで評価

### 自己チェック（評価ループ前のプリフライト）

サブエージェントに渡す前に、生成者側で最低限のチェックを通す:

- **Swap Test**: ブランド名を置き換えても気づかれないなら固有の「署名」を加える
- **Squint Test**: 半目で視覚的階層が読み取れるか
- **Signature Test**: 記憶に残る独自要素があるか
- **Token Test**: デザイントークンがシステムに従っているか

プリフライトで明らかな問題があれば、サブエージェント起動前に修正する（無駄なイテレーションを避ける）

---

## Phase 7: アクセシビリティ（WCAG 2.1 AA準拠）

**アクセシビリティは非交渉的要件。**

- **色コントラスト**: 通常テキスト 4.5:1、大テキスト 3:1、UI要素 3:1
- **キーボード操作**: Tab / Shift+Tab / Enter / Escape / Arrow で全操作可能
- **フォーカス表示**: `:focus-visible` で明確なアウトライン（2px以上）
- **Touch target**: モバイルで最小 44x44px
- **スクリーンリーダー**: 意味のある `aria-label`、ランドマーク、見出し階層
- **減モーション対応**: `prefers-reduced-motion` メディアクエリ

-> 詳細なWCAGガイドラインは `references/accessibility.md` を参照

---

## Phase 8: レスポンシブ設計

**Mobile-first アプローチを採用する。**

1. **モバイルファースト**: `min-width` メディアクエリで拡張
2. **Fluid Typography**: `clamp()` で滑らかなスケーリング
3. **レイアウト適応**: Grid / Flexbox で画面サイズに応じた構造変更
4. **タッチ最適化**: ボタン・リンクの十分なサイズとスペーシング

-> 詳細なブレークポイントパターンは `references/responsive.md` を参照

---

## 複数案提示（大規模変更時）

| プラン | アプローチ | リスク |
|--------|-----------|--------|
| **A: Progressive** | 既存デザインの段階的改善。最小変更、低リスク | 低 |
| **B: Radical** | フレームワークを壊す大胆な再設計。野心的 | 中 |
| **C: Ideal** | リソース制約なしの理想形。長期ビジョン | 高 |

各プランにモックアップまたは詳細説明を添え、ユーザーに選択を委ねる。

---

## アンチパターン

### 絶対にやらない

- ドラマチックなドロップシャドウ / 小要素に大ラジアス（16px+） / 非対称パディング
- 色付き背景上の純白カード / 装飾用太ボーダー（2px+） / 過剰スペーシング（48px+）
- スプリング・バウンシーアニメーション / 装飾グラデーション / 複数アクセントカラー
- **紫グラデーション + 白背景（AIっぽい）** / **Inter, Arial, Robotoデフォルト依存**
- **汎用 `#3B82F6` ブルー、teal-coral コンボ** / **Glassmorphism濫用、テンプレート的レイアウト**

### 常に自問する

デフォルトに逃げていないか？ / コンテキストとユーザーに合っているか？ / 深度戦略は一貫して意図的か？ / すべてがグリッド上にあるか？ / 何が記憶に残るか？

---

## 実装チェックリスト

**前**: system.md確認 / 方向性決定 / カラー選択 / タイポグラフィ決定 / 深度戦略選択
**中**: 4pxグリッド / 対称パディング / ラジアス一貫 / 意味のみの色使用 / データにモノスペース / WCAG AA
**後**: 評価ループPASS (≥25/35) / レスポンシブ / ダークモード / キーボード / ナビコンテキスト / system.md保存提案

---

## Context7 Library IDs

React(`/facebook/react`), Next.js(`/vercel/next.js`), Tailwind(`/tailwindlabs/tailwindcss`), shadcn/ui(`/shadcn-ui/ui`), Radix(`/radix-ui/primitives`), Framer Motion(`/framer/motion`)

---

## 出典

frontend-design(Anthropic), claude-design-skill(Dammyjay93), ui-ux-pro-max-skill(nextlevelbuilder), interface-design(Dammyjay93), bencium-claude-code-design-skill(bencium), claude-designer-skill(joeseesun), v0 System Prompt(Vercel)

**Remember: Claude is capable of extraordinary creative work.**
