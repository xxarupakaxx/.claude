---
name: design-eval-loop
description: ユーザーが Generator–Evaluator の反復でフロントエンドを改善するよう明示したときに使う。実ページを操作した独立評価、bounded な Refine / Pivot、最終スクリーンショットを必要とする。通常の UI 実装や一度のレビューには使わない。
---

# Design Eval Loop

生成と評価を分け、実ページの観測結果を次の修正へ渡す。対象はユーザーが指定した HTML、component、または URL と、今回のデザイン品質を判断する rubric である。`playwright-cli` と対象を起動できる環境がない場合は、可能な静的確認だけを行い、反復完了とは言わない。

## Phase A: 仕様を固定する

`designing-ui-ux` の必要な mode だけを読み、目的、利用者、主要 flow、visual direction、color / type / depth の基盤、保持する機能契約を一枚の `spec.md` に整理する。既存の `.interface-design/system.md` があれば先に読む。仕様が曖昧で Done が変わる場合だけ質問し、決まっていない好みを評価基準へ混ぜない。

```markdown
# Design Spec
## Product: <名前>
## Direction: <personality / tone>
## Foundation: <color / typography / depth>
## Target: <path or URL>
## Core flow: <実ページで確認する経路>
## Pass checks: <観測可能な基準>
```

## Phase B: Generate–Evaluate

### Generator

Iteration 1 は spec の core flow を満たす最小の実装を作る。以降は評価の `FIX` だけを根拠に **REFINE**（同じ方向を磨く）または **PIVOT**（仕様を保った別方向）を選ぶ。`KEEP` を壊さず、未要求の feature、fake data、placeholder を完成扱いにしない。

各回の変更は対象 scope 内に限定し、既存 workflow が定める checkpoint を使う。毎回の `git commit` や `git revert` を自動で要求しない。巻き戻しが必要なら、現在の変更を保存したうえでプロジェクトの gate とユーザーの write scope に従う。

### Browser

単体 HTML なら、対象 path を確認して次を使う。dev server はリポジトリが定める command を調べ、`npm run dev` などを推測して起動しない。

```bash
playwright-cli open
playwright-cli goto file:///path/to/output.html
```

実際の UI を操作し、主要な navigation、button、scroll、loading / error / empty を core flow の範囲で確認する。レスポンシブ要件がある場合だけ 375×812、768×1024、1440×900 など対象 project の viewport を使う。

### Evaluator

Generator と別コンテキストの read-only reviewer を使える場合は、対象、diff、spec、スクリーンショット、必要な rubric 参照だけを渡す。`references/evaluator-rubric.md` は採点が必要な回だけ、`references/strategy-guide.md` は戦略判断が必要な回だけ読む。本文をプロンプトへ丸ごと複写しない。独立 reviewer が起動できなければ、その欠落を記録し、自己評価を独立評価として扱わない。

Evaluator は実ページを操作し、必要な viewport のスクリーンショットと `file:line` 付きの観測を残す。

```markdown
## Evaluation — Iteration <N>
### Screenshots
- <viewport>: <path>
### Scores
| Criterion | Raw (1–5) | Weight | Weighted | Notes |
| --- | ---: | ---: | ---: | --- |
| Design Quality | | 2 | | |
| Originality | | 2 | | |
| Craft | | 1 | | |
| Functionality | | 1 | | |
| **Total (/30)** | | | | |
### KEEP
- <変更しない部分>
### FIX
- <問題、path:line、具体的な修正>
### CONSIDER
- <任意の提案>
### Strategic Recommendation
<REFINE / PIVOT / PASS と根拠>
```

4基準の重み付き最大値は **30**（Design 10 + Originality 10 + Craft 5 + Functionality 5）。合計 `25/30` 以上は rubric 上の PASS 候補だが、core flow、a11y、responsive、runtime の事実が欠ければ合格扱いにしない。

### Strategy

- スコア上昇か、局所的な FIX で改善できるなら REFINE。
- 2回連続でスコアが `±1` 以内、または Design / Originality が低いままなら PIVOT を一度検討する。
- 別方向を試しても改善しない、仕様を変える必要がある、または `KEEP` と `FIX` が衝突するなら人間へ確認する。
- 最大反復は既定 **7回**。15回まで延長するのはユーザーが明示し、時間・コスト・検証を受け入れた場合だけ。差分、score、strategy、未解決 finding を `scores.md` または task memory へ追記する。

スコアが下がったら原因と前回の証拠を比較し、巻き戻しが安全にできる場合だけ別の修正を試す。評価が改善したという理由だけで、機能・性能・アクセシビリティを犠牲にしない。

## Phase C: 完了確認

最終回は、対象の core flow を実ページで再実行し、必要な viewport の screenshot、WCAG 2.1 AA に関係する focus / keyboard / contrast / reduced-motion、console / network の異常、主要な loading / error / empty を確認する。`system.md` の更新やデザイン判断の保存は提案として分け、既存契約を無断で書き換えない。

最終報告には、反復数、各スコアと戦略、独立評価の有無、修正した finding、未確認・残存リスク、最終スクリーンショットの path、`PASS` / `ESCALATE` を含める。外部公開、PR、commit、設定変更は明示された gate がある場合だけ行う。
