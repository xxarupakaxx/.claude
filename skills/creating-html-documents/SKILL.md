---
name: creating-html-documents
description: 日本語の計画書、技術解説、調査報告、変更レビュー、長文資料を、読みやすく自己完結したHTML文書として作成・編集する。ユーザーがHTML、視覚的な計画書、ブラウザで読む報告書、図・表・コード差分を含む説明資料、印刷可能な単一HTMLを求めたときに使う。複数Phaseの作業ではviewing-plansとRoadmapを併用し、進捗ビューと完成文書を分離する。
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
6. 配布条件: local単一file、隣接asset、印刷の要否。

複数Phaseの作業では、先に `viewing-plans` でRoadmapを生成する。Roadmapは目的・現在地・次Taskを示し、完成HTMLは判断と説明を担う。両者へ同じ本文を複製しない。

## 文書型を選ぶ

詳細は `references/document-system.md` を読む。

- `decision-plan`: 採用判断、現状と目標、比較根拠、実装Wave、受入条件、risk、rollback。
- `technical-explainer`: 結論、用語、構造、処理flow、制約、例、検証方法。
- `change-review`: 変更理由、before / after、重要差分、影響範囲、risk、検証。
- `research-report`: 結論、scope、方法、発見、限界、含意、推奨、source。

文書型は固定templateではない。各章に一つの問いを与え、その問いに合うvisual patternを一つ選ぶ。

## Visual patternを選ぶ

| 読者の問い | 主な表現 |
|---|---|
| 何を採用するか | decision band、比較matrix |
| 何が変わるか | before / after、diff |
| どう動くか | inline SVGのflow、sequence |
| どの順で進めるか | entry / work / exitを持つWave |
| 合格したか | acceptance matrix、evidence table |
| 正確な値は何か | table。必要時だけchartを添える |
| 用語・出典を確認したい | evidence rail、脚注、source list |

cardを先に並べない。同じ状態をbadge、card、summary、diagramで重複表示しない。文章で十分ならvisualを増やさない。

## 作成手順

1. `assets/editorial-document.html` を基礎にする。既存HTMLの編集ではfilenameを変えない。
2. 文書型に応じて章を選び、不要なplaceholderとcomponentを削る。
3. 中心主張と現在地を最初のviewportに置く。背景説明から始めない。
4. 本文をprimary surfaceにする。wideでは約68–76字幅、補助railは250–310pxを目安にする。
5. 図はinline SVGを正本にし、`title`、`desc`、captionを付ける。Mermaid runtimeを新規導入しない。
6. codeはescapeし、言語classまたは明示labelを付ける。変更は理由の直後にdiffとして置く。
7. 表は見出しcellへ`scope`を付け、狭幅では局所scrollまたは意味順を保つstackへ変える。
8. 出典は主張の近くに置き、末尾のsource listへ接続する。sourceの内容と会話上の推測を混ぜない。
9. `references/validation.md` のgateを通す。
10. 検証合格後、ユーザーが自動表示を不要と明示していなければ、生成fileの絶対pathをhostのplatform openerで開く。macOSでは`/usr/bin/open "<absolute-path>"`、Linux desktopでは`xdg-open "<absolute-path>"`、Windows PowerShellでは`Start-Process "<absolute-path>"`を使う。
11. browser表示の成否、生成fileの絶対path、文書型、検証結果、残る制約を報告する。openerがない、非対話環境である、または起動に失敗した場合は、黙って成功扱いせず理由と絶対pathを示す。

## 自己完結を既定にする

- system / local fontを使う。
- CSSは単一HTMLへinlineする。
- 画像はinline SVG、data URI、またはユーザーが指定した隣接local assetを使う。
- remote font、CDN、analytics、remote image、外部runtimeを既定では読み込まない。
- scriptは内容に不可欠なinteractionがある場合だけ追加する。static文書はscript 0を優先する。
- CSPを付ける。static単一fileの既定は `default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'` とする。
- HTML自身へbrowser起動用のscript、redirect、shellを埋め込まない。browserを開く責務は、検証後にhost側のplatform openerが担う。
- clipboard、PDF shell、公開script、git commit / pushはHTML生成と別能力である。明示依頼と個別gateなしに実行しない。

## 視覚言語

- 長文はeditorial寄りにし、dashboardのKPI card群へ変換しない。
- hierarchyは見出し、余白、rule、位置で作る。radius、shadow、色の種類を増やして作らない。
- accentは1色を基本とし、警告、追加、削除など意味が異なる場合だけ補助色を使う。
- gradient、glass、装飾pill、意味のないicon、過剰なmotionを既定にしない。
- 日本語本文は15–17px、line-height 1.75–1.95を起点に実画面で調整する。
- mobileでは本文→根拠→用語のDOM順を保つ。hoverだけに情報を置かない。
- printではnavigationやstickyを解除し、URL、caption、表見出し、読み順を保つ。

## 完了条件

次を確認できるまで完成と報告しない。

- 3秒でpage purpose、中心主張、現在地を区別できる。
- 375px、768px、1440pxでdocument全体の横overflowが0。
- 200% zoomで主要情報を失わない。
- heading level skip、duplicate id、見出しなしtableが0。
- keyboard focusが見え、主要情報がhover専用でない。
- contrast、色以外の意味表示、forced colors、reduced motionを考慮する。
- print previewで本文、図、表、railの読み順が壊れない。
- 外部resourceは依頼で許可されたものだけ。既定は0。
- 制作過程やpromptの痕跡が本文に残らない。
- 明示的なopt-outがない限り検証済みfileをbrowserで開き、起動できない環境では失敗理由と絶対pathを報告する。

見た目の好みだけで合格にしない。中心主張の理解、根拠到達、responsive、印刷、安全性を同じrubricで確認する。
