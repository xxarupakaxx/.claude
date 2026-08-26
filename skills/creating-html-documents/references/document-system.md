# HTML文書system

## Decision plan

最初のviewportで「何を採用するか」「現在どこか」「何が次のgateか」を判断できるようにする。

推奨順序:

1. 中心主張とstatus。
2. 現状と目標。
3. 選択肢の比較と採否理由。
4. 目標構造。
5. entry / work / exitを持つ実装Wave。
6. acceptanceとevidence。
7. risk、停止条件、rollback。
8. sourceと用語。

Task一覧だけを計画書と呼ばない。誰が何をするかだけでなく、なぜ、その順なのか、何をもって次へ進むのかを書く。

## Technical explainer

推奨順序:

1. 一文の結論。
2. 読者が先に必要とする最小用語。
3. 全体構造の図。
4. 入力から出力までのflow。
5. 重要なinterfaceまたはdata。
6. 制約とfailure mode。
7. 具体例。
8. 検証方法とsource。

定義を用語集へ隔離しすぎない。初出の近くでも短く説明し、railは参照用にする。

## Change review

推奨順序:

1. 変更の理由と影響。
2. before / afterの要約。
3. 変更箇所ごとの説明とdiff。
4. data / API / UIへの影響。
5. migration、compatibility、rollback。
6. test evidence。
7. 残るrisk。

diffだけを並べず、読者が先に理由と影響を理解できるようにする。

## Research report

推奨順序:

1. 結論と次の一手。
2. scope、母集団、方法。
3. 主要発見。
4. 比較またはevidence map。
5. 限界と誤読しやすい点。
6. 含意と推奨。
7. source list。

事実、推論、提案を構造で区別する。数字は意味まで翻訳し、読者に再計算させない。

## 共通component

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
