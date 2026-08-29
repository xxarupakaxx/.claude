---
name: creating-html-documents
description: 日本語の計画書、技術解説、調査報告、変更レビュー、長文資料を、具体的な根拠・仕組み・境界・含意まで読めるdesktop向け自己完結HTMLとして作成・編集する。ユーザーがHTML、ブラウザで読む報告書、図・表・コード差分を含む説明資料を求めたときに使う。mobile、印刷、PDFは明示依頼時だけ扱う。
---

# HTML文書を作成する

MarkdownをHTMLで包むのではなく、読者が判断・理解・検証しやすい文書を作る。

## 最初に決める

HTMLを書く前に次を一行ずつ確定する。

1. 読者: 誰が読むか。
2. 目的: 読後に何を理解または判断するか。
3. 文書型: `decision-plan`、`technical-explainer`、`change-review`、`research-report` のどれか。
4. 中心主張: 冒頭だけで伝える結論。
5. 根拠: 事実、比較、図、差分、出典のどれが主張を支えるか。
6. 配布条件: local単一file、隣接asset、desktop以外の対応要否。

複数Phaseの作業では、先に `viewing-plans` でRoadmapを生成する。Roadmapは目的・現在地・次Taskを示し、完成HTMLは判断と説明を担う。両者へ同じ本文を複製しない。

## 文書型を選ぶ

詳細は `references/document-system.md` を読む。

- `decision-plan`: 採用判断、Overview-first gate該当時のorientation / overview、現状と目標、比較根拠、実装Wave、受入条件、risk、rollback。
- `technical-explainer`: 結論、Overview-first gate該当時のorientation / overview、用語、処理flow、制約、例、検証方法。
- `change-review`: 変更理由、Overview-first gate該当時のorientation / overview、before / after、重要差分、影響範囲、risk、検証。
- `research-report`: 結論、Overview-first gate該当時のorientation / overview、scope、方法、発見、限界、含意、推奨、source。

文書型は固定templateではない。各章に一つの問いを与え、その問いに合うvisual patternを一つ選ぶ。

## 先に中身を抽出する

HTML構造や図を作る前に、source inventoryとclaim ledgerをcompactな作業メモとして作る。

- source inventory: file、section、symbol、差分、test、外部sourceのどこが何を裏付けるか。
- claim ledger: 主要主張、具体的な事実、仕組みまたは因果、境界・反例、読者への含意、source anchor。

各主要主張は、少なくとも具体的な根拠、仕組み、読者への含意へ接続する。境界条件や反例がmaterialなら省略しない。sourceで確認できない内容は、事実として補完せず推論または未確認と表示する。

文書型ごとのdetail unitは次を最低粒度にする。

| 文書型 | detail unitに含めるもの |
|---|---|
| decision-plan | 選択肢、成立mechanism、採否理由、trade-off、entry / exit、failure、rollback、evidence |
| technical-explainer | input、具体的な処理、branch条件、data contract、state / side effect、failure / recovery、source |
| change-review | file / symbol、before / after、変更理由、caller / downstream impact、compatibility、test evidence |
| research-report | sourceごとの主張、evidence quality、比較軸、代表case、反例・限界、実務上の含意 |

「処理する」「連携する」「最適化する」「対応する」のような抽象語だけでdetailを閉じない。主体、対象、条件、観測可能な結果まで具体化する。長文化やsection数を情報量の代替にせず、同じ内容の言い換えを削る。

## Orientationとoverviewは索引にする

workflow、architecture、lifecycle、before / after、dependency、failure pathなどを説明し、3つ以上の相互作用するactor、component、stage、state、責務、dependencyが関係する文書では、中心主張の直後にorientationとaccessibleなinline SVG overviewを置く。欠如時failureが複数箇所へ伝播する場合も同じ扱いにする。単にfileやevidenceが3件あるだけでは発火しない。

orientationは長い背景説明ではない。次の5点を短く並べ、読者が「なぜ読むか」と「全体のどこを見ているか」を先に掴めるようにする。

1. 背景: この文書が必要になった状況。
2. without-this failure: この理解や変更がない場合に何が壊れるか。
3. 対象scope: どの境界、期間、system、file、機能を扱うか。
4. 目標状態: 読後または変更後に成立しているべき状態。
5. 全体内の位置: 対象が周辺actor、上流、下流、検証、運用のどこに接続するか。

overviewからdetailへ降りるzoom levelを固定する。

- Level 0: headerまたはdecision bandで中心主張を言い切る。
- Level 1: orientationで背景、without-this failure、scope、目標状態、全体内の位置を示す。
- Level 2: overview SVGで全体のactor / component / stage、主要flow、対象境界、failureの伝播先を一枚で示す。
- Level 3: detail sliceでoverview上の番号や名称を再利用し、一つのsubflow、before / after、failure path、diffだけを詳述する。
- Level 4: evidenceでtest、source、制約、残余riskを示す。

detailはoverviewと同じ名称、番号、境界名で接続する。overviewの情報を別図として再描画しない。overviewだけで説明を終えず、claim ledgerの具体的なdetail unit、evidence、含意へ降りる。detailで同じ情報を繰り返すだけなら、図を増やさず、該当番号への文章、table、diff、evidenceにする。

単一事実、単純な一操作、短い値比較、2要素だけのbefore / afterにはoverview SVGを強制しない。その場合も結論先行、scope、evidenceは保つ。

## Visual patternを選ぶ

| 読者の問い | 主な表現 |
|---|---|
| 何を採用するか | decision band、比較matrix |
| 全体のどこを見るか | orientation、overview SVG |
| 何が変わるか | before / after、diff |
| どう動くか | inline SVGのflow、sequence |
| ないと何が壊れるか | failure path、impact map |
| どの順で進めるか | entry / work / exitを持つWave |
| 合格したか | acceptance matrix、evidence table |
| 正確な値は何か | table。必要時だけchartを添える |
| 用語・出典を確認したい | evidence rail、脚注、source list |

cardを先に並べない。同じ状態をbadge、card、summary、diagramで重複表示しない。文章で十分ならvisualを増やさない。

## 作成手順

1. source inventoryとclaim ledgerを作り、根拠不足と未確認を分離する。
2. `assets/editorial-document.html` を基礎にする。既存HTMLの編集ではfilenameを変えない。
3. 文書型に応じて章を選び、不要なplaceholderとcomponentを削る。
4. 中心主張と現在地を最初のviewportに置く。背景説明から始めない。
5. orientation triggerに該当する場合だけ、中心主張の直後に短いorientationとoverview SVGを置く。
6. claim ledgerのdetail unitを本文へ展開する。重要な主張は具体例、境界、evidence、含意へ接続する。
7. 本文をprimary surfaceにする。desktopでは約68–76字幅、補助railは250–310pxを目安にする。
8. 図はinline SVGを正本にし、`role="img"`、`title`、`desc`、captionを付ける。Mermaid runtimeを新規導入しない。
9. codeはescapeし、言語classまたは明示labelを付ける。変更系文書では、変更理由の直後に関連diffを示す。
10. 表は見出しcellへ`scope`を付ける。
11. 出典は主張の近くに置き、末尾のsource listへ接続する。sourceの内容と会話上の推測を混ぜない。
12. `references/validation.md` のgateを通す。
13. 検証合格後、ユーザーが自動表示を不要と明示していなければ、生成fileの絶対pathをhostのplatform openerで開く。
14. browser表示の成否、生成fileの絶対path、文書型、検証結果、残る制約を報告する。

## 自己完結を既定にする

- system / local fontを使う。
- CSSは単一HTMLへinlineする。
- 画像はinline SVG、data URI、またはユーザーが指定した隣接local assetを使う。
- remote font、CDN、analytics、remote image、外部runtimeを既定では読み込まない。
- scriptは内容に不可欠なinteractionがある場合だけ追加する。static文書はscript 0を優先する。
- CSPを付ける。static単一fileの既定は `default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'` とする。
- HTML自身へbrowser起動用のscript、redirect、shellを埋め込まない。browserを開く責務は、検証後にhost側のplatform openerが担う。
- clipboard、PDF生成、印刷最適化、公開script、git commit / pushはHTML生成と別能力である。明示依頼と個別gateなしに実行しない。

## 視覚言語

- 長文はeditorial寄りにし、dashboardのKPI card群へ変換しない。
- hierarchyは見出し、余白、rule、位置で作る。radius、shadow、色の種類を増やして作らない。
- accentは1色を基本とし、警告、追加、削除など意味が異なる場合だけ補助色を使う。
- gradient、glass、装飾pill、意味のないicon、過剰なmotionを既定にしない。
- 日本語本文は15–17px、line-height 1.75–1.95を起点に実画面で調整する。
- 既定は1440x900前後のPC閲覧とする。mobile responsive、tablet調整、print stylesheet、PDF exportは明示依頼時だけ追加する。
- hoverだけに主要情報を置かない。

## 完了条件

次を確認できるまで完成と報告しない。

- 3秒でpage purpose、中心主張、現在地を区別できる。
- 1440x900で意図しない横overflow、text overlap、clipがない。
- heading level skip、duplicate id、見出しなしtableが0。
- keyboard focusが見え、主要情報がhover専用でない。
- contrastと色以外の意味表示を考慮する。
- 外部resourceは依頼で許可されたものだけ。既定は0。
- 制作過程やpromptの痕跡が本文に残らない。
- orientation triggerに該当する文書では、中心主張直後のorientation、accessible overview SVG、対応するdetail slice、evidenceが同じ名称や番号で接続している。
- 各主要主張が具体的な根拠、仕組み、読者への含意へ接続し、materialな境界条件または反例が落ちていない。
- technical flowではinput、branch、data / state、side effect、failure / recovery、sourceを追える。
- overview、見出し、一般論だけで本文を埋めていない。
- triggerに該当しない単純文書では、図を省いた理由が文書構造上自然で、結論、scope、根拠が不足していない。
- 明示的なopt-outがない限り検証済みfileをbrowserで開き、起動できない環境では失敗理由と絶対pathを報告する。

見た目の好みだけで合格にしない。中心主張、具体的detail、根拠到達、含意、安全性を確認する。mobile、print、PDFは依頼された場合だけ追加rubricを適用する。
