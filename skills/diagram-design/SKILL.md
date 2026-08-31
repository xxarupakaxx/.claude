---
name: diagram-design
description: Create source-backed static dependency, processing, architecture, or comparison diagrams for plan documents as self-contained HTML/SVG when spatial relationships add information beyond prose or a table; do not own roadmap progress, task order, or canonical state diagrams.
license: MIT
metadata:
  version: "2.6-adapted.1"
---

# Diagram Design（計画書用適合版）

計画書の実装内容を、読者が「何が何に依存し、どこで処理され、何が変わるか」まで追える静的図にする。図は説明の代わりではなく、関係・順序・境界が文章や表より速く読める場合だけ使う。

この入口は日本語の短い判断規則と、図種ごとの参照先だけを常時読む。詳細な座標規則は選んだ図種の reference を必要時に読む。

## 使う条件

次の全てが揃ったときに使う。

- 読者、問い、根拠となる source、図に含めない範囲が確定している。
- 依存、処理の受け渡し、構造の境界、または二つの状態の差が空間配置に意味を持つ。
- 各ノードと線を source anchor（`path#Lx-Ly` または task artifact の該当行）へ戻せる。
- 出力を SVG 正本と、同じ SVG を含む自己完結 HTML で渡せる。

## 使わない条件

- 3列程度の表、短い箇条書き、単純な Before / After で同じ内容を伝えられる。
- Roadmap の進捗、task 順、session 選択、完了状態を表示するだけである。これは `viewing-plans` の責務。
- canonical な状態機械・状態遷移・実行順序を別の owner が管理している。
- 根拠がなく、見た目のためにノード・線・数値を補うことになる。

## 作成手順

1. 問い、読者、source anchor、未知・除外範囲を短く書く。
2. まず semantic pattern、次に visual type を選ぶ。選択表は `references/selection.md`。
3. `references/output-contract.md` で size、detail、audience、fidelity ledger を決める。
4. 選んだ図種の reference を一つだけ読み、`references/visual-rules.md` の共通規則を適用する。
5. source の事実だけで入力を作り、同じ id を保持して SVG を生成する。比較では Before と After の対応を同じ id で表す。
6. SVG を正本として保存し、HTML には同じ SVG、短い読み方、source anchor、テキスト fallback を初期表示する。
7. `references/quality-gate.md` を満たすか確認する。実測していない効果や採用状態は書かない。

## 図種の選択

| 読者が知りたいこと | pattern / type | JIT 参照 |
|---|---|---|
| 共有依存、fan-in、cycle | dependency graph | `references/type-dependency.md` |
| 複数の担当をまたぐ入力・処理・出力 | data flow / process | `references/type-process.md` |
| zone、component、trust boundary | architecture | `references/type-architecture.md` |
| 二つの状態、ルール差、Before / After | comparison。表を第一候補、必要なら paired trace | `references/type-comparison.md` |

behavior、state、risk が中心なら `references/selection.md` の pattern を一つだけ選ぶ。二つの pattern を完全に重ねず、必要なら overview と detail に分ける。

## 共通出力契約

- `<svg>` は `viewBox`、`role="img"`、`aria-labelledby`、空でない `<title>` と `<desc>` を持つ。
- HTML と SVG は外部 stylesheet、画像、icon、font、script、iframe、`foreignObject`、network request を持たない。
- font は system stack を使う。日本語本文は `Hiragino Sans`、`Yu Gothic`、`Noto Sans JP`、`system-ui` の順を基本にする。
- HTML は inline CSS と inline SVG だけで完結し、CSP で script、font、connect、object を禁止する。
- 線は原則として直交し、線を先に描いてから node を描く。線の label には紙色の mask を置く。色だけを意味にしない。
- accent は一つか二つの焦点に限る。影、強い glow、全 node の同色強調、斜め線、巨大な凡例を使わない。
- source が不明な値は `unknown` と書き、推測で名前や状態を補わない。削減・統合・除外は fidelity ledger に残す。

## 型別の上限

- dependency: 9 nodes、14 edges、4 ranks、強調 cycle は1つまで。tree 形なら tree を使う。
- process: 最大6 lanes、12 steps。lane は担当、step は順序を表し、空 cell は描かない。
- data flow: 最大4 lanes、6 steps、focal handoff は1つ。payload の input / output を明示する。
- architecture: 最大3 zonesを基本とし、trust boundary と主経路を分ける。
- comparison: 単純差分は表。paired trace は exactly 2 traces、3–6 rules、first divergence は1つ。数値 slopegraph は同単位・同尺度の2状態だけ。

上限を超える場合は文字を縮めず、leaf の統合・overview/detail 分割・表への切替を行う。

## 参照と責務

この適合版は公式候補の考え方を参照するが、公式 212 file の実行環境や全39 typeを提供するものではない。source、採用差分、除外機能は `SOURCE` と `ADAPTATION.md` に記録する。Roadmap の本文、task 順、進捗、Hub は `viewing-plans` と共通 renderer の責務であり、この Skill は本文内の説明図を担当する。
