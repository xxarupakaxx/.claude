# HTML文書system

## Overview-first gate

workflow、architecture、lifecycle、before / after、dependency、failure pathなど、3つ以上の相互作用するactor、component、stage、state、責務、dependencyの関係を理解しないと判断できない文書では、中心主張の直後にorientationとaccessibleなinline SVG overviewを置く。欠如時failureが複数の下流へ伝播する場合も必須にする。単にfileやevidenceが3件あるだけでは発火しない。

orientationは背景、without-this failure、対象scope、目標状態、全体内の位置を短く示す。overview SVGは全体のactor / component / stage、主要flow、対象境界、failureの伝播先を一枚で示す。detail sliceはoverviewの番号、名称、境界を再利用し、一つのsubflow、before / after、failure path、diffへzoomする。overviewの再描画や同じ情報の重複表示はしない。

単一事実、単純な一操作、短い値比較、2要素だけのbefore / afterには図を強制しない。図を省く場合も結論、scope、根拠の位置は崩さない。

## Decision plan

最初のviewportで「何を採用するか」「現在どこか」「何が次のgateか」を判断できるようにする。

推奨順序:

1. 中心主張とstatus。
2. Overview-first gate該当時のorientation: 背景、without-this failure、scope、目標状態、全体内の位置。
3. Overview-first gate該当時のoverview SVG: 対象system、decision point、主要dependency、failureの伝播先。
4. 現状と目標。
5. 選択肢の比較と採否理由。
6. Overview-first gate該当時のdetail slice: 目標構造または重要な移行flow。
7. entry / work / exitを持つ実装Wave。
8. acceptanceとevidence。
9. risk、停止条件、rollback。
10. sourceと用語。

Task一覧だけを計画書と呼ばない。誰が何をするかだけでなく、なぜ、その順なのか、何をもって次へ進むのかを書く。

## Technical explainer

推奨順序:

1. 一文の結論。
2. Overview-first gate該当時のorientation: 背景、without-this failure、scope、目標状態、全体内の位置。
3. Overview-first gate該当時のoverview SVG: 全体構造と主要flow。
4. 読者が先に必要とする最小用語。
5. Overview-first gate該当時のdetail slice: 入力から出力までのflow、重要なinterface、data。
6. 制約とfailure mode。
7. 具体例。
8. 検証方法とsource。

定義を用語集へ隔離しすぎない。初出の近くでも短く説明し、railは参照用にする。

## Change review

推奨順序:

1. 変更の理由と影響。
2. Overview-first gate該当時のorientation: 背景、without-this failure、scope、目標状態、全体内の位置。
3. Overview-first gate該当時のoverview SVG: 変更対象、上流、下流、検証、rollback point。
4. before / afterの要約。
5. Overview-first gate該当時のdetail slice: overview上の番号に対応する変更箇所ごとの説明とdiff。
6. data / API / UIへの影響。
7. migration、compatibility、rollback。
8. test evidence。
9. 残るrisk。

diffだけを並べず、読者が先に理由と影響を理解できるようにする。

## Research report

推奨順序:

1. 結論と次の一手。
2. Overview-first gate該当時のorientation: 調査対象が全体のどこにあり、未理解だと何を誤判断するか。
3. Overview-first gate該当時のoverview SVG: 複数source、actor、判断軸の関係。必要ならevidence mapとして描く。
4. scope、母集団、方法。
5. 主要発見。
6. Overview-first gate該当時のdetail slice: 比較、代表case、反例。
7. 限界と誤読しやすい点。
8. 含意と推奨。
9. source list。

事実、推論、提案を構造で区別する。数字は意味まで翻訳し、読者に再計算させない。

## 共通component

### Orientation

中心主張の直後に置き、背景、without-this failure、対象scope、目標状態、全体内の位置を短く示す。長い経緯、作業日誌、網羅的な前提列挙へ膨らませない。

### Overview SVG

3つ以上の相互作用する要素関係、状態遷移、failure伝播を一枚で示す。`role="img"`、`title`、`desc`、captionを持つinline SVGにする。Mermaid、remote resource、runtime scriptを前提にしない。

### Detail slice

overviewの番号、名称、境界を再利用し、一つのsubflow、before / after、failure path、diffだけを詳述する。overviewと同じ全体図を描き直さない。

### Decision band

一つの採用判断と、一つの現在statusだけを置く。複数のKPIを並べない。

### Evidence rail

本文の補助であり、別の主役ではない。wideではstickyにできる。narrowとprintでは本文後へ送る。

### Comparison matrix

選択肢を共通軸で比べる。各案のメリット・デメリットを別々に列挙しない。

### Wave route

各Waveにentry、work、exitを持たせる。単なる番号付きTaskと区別する。

### Figure

図、caption、sourceを一体にする。diagram内の色だけに意味を依存させず、labelと形でも区別する。

### Diff

追加、削除、contextを行単位で示す。赤緑だけでなく記号とlabelを併用する。

### Table

正確な値、責務、比較に使う。cardへ分解すると横比較が難しくなる場合はtableを保つ。
