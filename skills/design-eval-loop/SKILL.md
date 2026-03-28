---
name: design-eval-loop
description: |
  Generator-Evaluator反復ループでフロントエンドデザインを自律的に改善するスキル。
  Anthropic "Harness Design for Long-Running Apps" パターンの実装。
  GeneratorがHTML/CSS/JSを生成し、独立したEvaluatorがPlaywrightで実ページを操作・採点・批評。
  フィードバックをGeneratorに返し、Refine/Pivot戦略で5-10回反復する。
  「デザインループで作って」「反復ループで改善して」「design-eval-loopして」等の依頼に対応。
---

# Design Eval Loop

Generator-Evaluator反復ループによるフロントエンドデザインの自律的改善。
GANに着想を得たアーキテクチャ: 生成と評価を分離し、フィードバックで品質を引き上げる。

出典: Anthropic Engineering "Harness Design for Long-Running Apps"

---

## 前提条件

- `playwright-cli` が利用可能であること
- dev serverが起動可能なプロジェクトであること（または単体HTMLファイル）
- `designing-ui-ux` スキルの references/ が利用可能であること

---

## Phase A: Planner（製品仕様 + デザイン方向性）

`designing-ui-ux` の Phase 0-3 を適用する。

### A.0 デザインメモリの確認

PJルートの `.interface-design/system.md` を確認する（`designing-ui-ux` Phase 0）。
- **存在する場合**: 読み込み、確立済みの Direction / Tokens / Patterns を適用
- **存在しない場合**: Phase A.2-A.3 で基盤確立後、保存を提案

### A.1 製品仕様の展開

ユーザーの短いプロンプト（1-4文）を完全な製品仕様に展開。

- `designing-ui-ux` Phase 1 (Planner) の手順に従う
- AskUserQuestionで仕様を確認

### A.2 デザイン方向性の決定

- `designing-ui-ux` Phase 2 のコンテキスト分析（4つの問い）を実行
- デザインパーソナリティを選択
- トーンを決定

### A.3 デザイン基盤の確立

- `designing-ui-ux` Phase 3 のカラー/タイポグラフィ/深度を決定
- `.interface-design/system.md` があれば読み込み

### 出力

以下をメモリディレクトリに `spec.md` として保存:

```markdown
# Design Spec
## Product: {名前}
## Direction: {パーソナリティ + トーン}
## Foundation: {カラー / タイポグラフィ / 深度}
## Target: {ファイルパス or URL}
```

---

## Phase B: Generate-Evaluate ループ（コア）

### ループ構造

```
Iteration 1
  │
  ├─ [Generator] designing-ui-uxの原則でHTML/CSS/JS生成
  │     ↓
  ├─ [Server] dev server起動 or ファイルサーブ
  │     ↓
  ├─ [Evaluator] 独立サブエージェント（playwright + ルーブリック）
  │     ↓ スコア + 批評
  ├─ [Strategy] Refine / Pivot / Pass 判定
  │     ↓
  └─ → Iteration 2 ... N
```

### B.1 Generator（生成フェーズ）

**初回（Iteration 1）**: Phase Aの仕様に基づきHTML/CSS/JSを生成。

- `designing-ui-ux` Phase 4-5 のクラフト原則・コンポーネント設計を適用
- 単体HTMLファイル or プロジェクト内コンポーネント
- `designing-ui-ux` のアンチパターンを回避
- 生成後、必ずgit commitを打つ（REVERTに備える）

**2回目以降**: Evaluatorのフィードバックに基づき修正。

- **REFINEモード**: 現在の方向性を維持しつつ、批評の具体的指摘を修正
- **PIVOTモード**: デザイン方向性を根本的に変更。新しい美学・レイアウト・インタラクションを探索
- 修正後、毎回git commitを打つ

### Generatorのコンテキスト管理

Generatorはメインセッションのコンテキストで動作する。ループが長くなるとコンテキスト窓が圧迫されるため、以下で対応:

1. **各イテレーションでの情報管理**:
   - spec.md（Phase A出力）: 不変。常に参照可能
   - scores.md: 各イテレーションのスコアを追記記録
   - 直前のEvaluatorフィードバック: 次のイテレーションの入力
   - **過去のフィードバックは要約して保持**（全文は不要）

2. **コンテキスト窓が枯渇した場合**（/clear が必要になったら）:
   - scores.md を Read して過去の推移を把握
   - spec.md を Read して仕様を復元
   - 直前のEvaluatorフィードバック（メモリディレクトリに保存済み）を Read
   - 現在のコードを Read して状態を把握
   - 中断したイテレーション番号から再開

3. **メモリディレクトリへの保存**:
   - 各Evaluatorの出力を `eval-iter-{N}.md` として保存
   - PIVOTした場合は `pivot-{N}-reason.md` として方向転換の理由を保存

### B.2 Server（サーブフェーズ）

生成物をブラウザで確認可能にする:

```bash
# 単体HTMLの場合
playwright-cli open
playwright-cli goto file:///path/to/output.html

# dev serverがある場合
# npm run dev 等でサーバー起動後
playwright-cli open
playwright-cli goto http://localhost:3000
```

### B.3 Evaluator（評価フェーズ）

**CRITICAL: Evaluatorは必ず独立したサブエージェントとして起動する。Generatorと同一コンテキストで評価しない。**

理由: 自己評価バイアスの排除。「自分のエッセイを校正するようなもの — 技術的には可能だが、実際には非効率」

#### Evaluatorサブエージェントの起動方法

**Agentツール** で `ui-ux-reviewer` サブエージェントを起動する:

```
Agent(
  subagent_type: "ui-ux-reviewer",
  model: "sonnet",  # model-routing.md準拠: UI/UXレビューはsonnet
  description: "Design evaluation iteration {N}",
  prompt: <<以下のプロンプト>>
)
```

**プロンプト内容**:

```
あなたは懐疑的なデザイン評価者です。デフォルトで問題を探してください。

## タスク
以下のページをPlaywrightで操作し、スクリーンショットを撮影した上で評価してください。

## 対象
URL: {URL or file path}

## 評価手順
1. playwright-cli open → goto {URL}
2. ページ全体のスクリーンショットを撮影
   playwright-cli screenshot --filename={メモリディレクトリ}/screenshot-iter{N}-desktop.png
3. 主要なインタラクション（ナビゲーション、ボタン、スクロール）を実行
4. 3ビューポートでレスポンシブ確認:
   - playwright-cli resize 375 812 → screenshot（モバイル）
   - playwright-cli resize 768 1024 → screenshot（タブレット）
   - playwright-cli resize 1440 900 → screenshot（デスクトップ）
5. 以下の4基準で採点（加重スコアリング）

### 採点基準
{evaluator-rubric.md の「4基準の加重スコアリング」セクション全文をここに展開}

### AIスロップ検出チェックリスト
{evaluator-rubric.md の「AIスロップの検出チェックリスト」をここに展開}

6. 具体的な批評を記述（ファイル・行番号・修正案付き）

## 出力フォーマット（必ずこの形式で）

### Scores
| Criterion | Raw | Weighted | Notes |
|-----------|-----|----------|-------|
| Design Quality | {1-5} | {x2} | {根拠} |
| Originality | {1-5} | {x2} | {根拠} |
| Craft | {1-5} | {x1} | {根拠} |
| Functionality | {1-5} | {x1} | {根拠} |
| **Total** | | **{/35}** | |

### KEEP（触らないこと）
- {具体的に}

### FIX（必ず修正）
- {問題}: {修正案。ファイル・行番号・CSS値等}

### CONSIDER（余裕があれば）
- {提案}

### Strategic Recommendation
{REFINE / PIVOT / PASS の推奨と理由}
```

**IMPORTANT**: ルーブリックの採点基準は references/evaluator-rubric.md から **全文をプロンプトに展開** して渡すこと。サブエージェントは references/ ファイルを自力で読めない場合がある。

#### Evaluatorの独立性を保証する設計

- Agentツールで起動されるサブエージェントは毎回新しいコンテキスト（自然なコンテキストリセット）
- Generatorの意図・苦労・試行錯誤を知らない状態で評価する
- 評価基準はルーブリックで固定し、プロンプトに埋め込むことでドリフトを防止

### B.4 Strategy（戦略判定フェーズ）

Evaluatorのスコアと過去のスコア推移に基づき判定:

```
スコア推移を確認:
  │
  ├─ 合計 ≥ 25/35 → PASS（ループ終了、Phase Cへ）
  │
  ├─ 前回比 +2以上 → REFINE（同じ方向性で修正）
  │     指示: 「Evaluatorの批評に基づき修正。Keepは触らない。」
  │
  ├─ 前回比 ±1以内 → 停滞カウント++
  │     ├─ 停滞1回目 → REFINE（もう1回だけ同じ方向で試す）
  │     ├─ 停滞2回目 → PIVOT（方向転換）
  │     └─ 停滞3回目 → ESCALATE（ユーザーに判断を委ねる）
  │
  └─ 前回比 -2以上 → REVERT + REFINE
        指示: 「前回の方が良かった。前回の状態に戻し、別の改善を試す。」
```

→ 判定の詳細は `references/strategy-guide.md` を参照

### イテレーション制御

| 設定 | デフォルト値 | 設定可能範囲 | 理由 |
|------|-------------|-------------|------|
| 最大イテレーション | **7** | 3-15 | コスト・時間とのバランス |
| PASS閾値 | **25/35** | 20-35 | デザイン品質3+独自性3以上 |
| 早期終了 | スコア30+ or Fix0件 | - | 十分な品質 |
| PIVOT上限 | **2回** | 1-3 | 際限ない方向転換を防止 |
| 連続停滞でエスカレーション | **3回** | 2-5 | ユーザーに判断を委ねる |

### スコア推移の記録

各イテレーションのスコアをメモリディレクトリに `scores.md` として追記:

```markdown
# Score History

| Iter | Design(x2) | Originality(x2) | Craft | Function | Total | Strategy |
|------|-----------|-----------------|-------|----------|-------|----------|
| 1    | 2 (4)     | 2 (4)           | 3     | 4        | 15    | REFINE   |
| 2    | 3 (6)     | 2 (4)           | 3     | 4        | 17    | REFINE   |
| 3    | 3 (6)     | 3 (6)           | 4     | 4        | 20    | REFINE   |
| 4    | 3 (6)     | 3 (6)           | 4     | 4        | 20    | PIVOT    |
| 5    | 4 (8)     | 4 (8)           | 4     | 4        | 24    | REFINE   |
| 6    | 4 (8)     | 4 (8)           | 4     | 5        | 25    | PASS     |
```

---

## Phase C: 最終出力

### C.1 成果物の確認

- 最終版のスクリーンショットを3ビューポートで撮影・保存
- WCAG 2.1 AAチェック（`designing-ui-ux` Phase 7）
- レスポンシブ確認（`designing-ui-ux` Phase 8）

### C.2 デザインメモリの更新

最終的なデザイン判断を `.interface-design/system.md` に保存提案。

### C.3 レポート

ユーザーに以下を報告:
- 最終スコアと推移グラフ（テキスト）
- 反復回数とPIVOT回数
- 最も効果的だった改善（スコア最大上昇のイテレーション）
- 最終スクリーンショットのパス

---

## `designing-ui-ux` との関係

| 観点 | `designing-ui-ux` | `design-eval-loop` |
|------|-------------------|-------------------|
| 目的 | 通常のUI実装 | デザイン品質の極限追求 |
| 評価 | Phase 6で3回まで | 5-15回の反復 |
| 評価方法 | コードレビュー中心 | Playwright実操作 |
| 戦略 | なし | Refine / Pivot |
| コスト | 低〜中 | 中〜高 |
| 使い分け | 日常のUI作業 | LP・ショーケース・コンペ等 |

**共通基盤**: Phase 2-5の原則、references/、アンチパターンはすべて`designing-ui-ux`から継承。

---

## 安全ガード

- **最大ループ回数**: デフォルト7（設定で最大15まで）
- **PIVOT上限**: 2回（無限の方向転換を防止）
- **連続停滞**: 3回連続±1以内でユーザーにエスカレーション
- **コスト意識**: 各イテレーションでサブエージェント1回起動。7回で概算$10-30
- **Generatorのコンテキスト**: メインセッションのコンテキストで動作。窓が埋まりそうなら手動で/clearし、spec.md + scores.md + 最新のフィードバックで再開
