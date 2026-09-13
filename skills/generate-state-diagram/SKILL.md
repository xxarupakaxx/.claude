---
name: generate-state-diagram
description: 既存branchやsystemからtrigger・guard・state変化・side effect・failure/recovery・source根拠を抽出し、SVG状態図と詳細ledgerを作る。状態図・処理フロー・domain modelの明示依頼で使い、静的SVGが正本になる。
triggers:
  - "状態図生成"
  - "state diagram"
  - "処理フロー図"
  - "フロー図"
  - "ドメインモデル図"
  - "domain model"
invocation: user
allowed-tools: Read, Bash, Glob, Grep, Write
---

# ブランチ状態図・処理フロー図

新しい図はSVGを正本とし、詳細をMarkdown ledgerへ置く。標準成果物は `91_state_diagram.svg` と `91_state_diagram.md`。Markdownから `![状態図](91_state_diagram.svg)` で参照する。PNG、PDF、mobile/print版、Mermaidは作らない。HTMLはユーザーが求めた場合、または図とledgerを同じ画面で読む必要がある場合だけ追加する。

## 使う範囲

Phase 5の完了報告、またはユーザーの明示依頼で、workflow、batch、state管理、外部連携、domain model、画面遷移を説明するときに使う。style・文言・テストだけ、設定/文書だけ、状態遷移のない単一関数変更なら省略できる。

## 調査

まず問いを1〜3件に絞り、対象branchと差分を確認する。

```bash
git diff <BASE_BRANCH>...HEAD --stat
git log <BASE_BRANCH>..HEAD --oneline
```

差分だけで完結させず、caller/callee、data model、test、設定、運用入口を必要な範囲で読む。描画前にevidence inventoryを作り、確認できない関係は `未確認` とする。

| 対象 | 記録する情報 |
| --- | --- |
| actor/component | 責務、input/output、owned state、source anchor |
| state | 意味、invariant、保存先、開始/終了条件 |
| transition | trigger、guard、before/after、effect、side effect、failure/recovery、source anchor |
| data/interface | field/payload、producer/consumer、validation、永続化 |
| external boundary | 呼出先、timeout、retry、idempotency、partial failure |

anchorは `path:line`、symbol、test名などへ戻せる形にする。`処理する` のような主体・対象・結果のないnode/edgeを作らない。

## 図の選択

core diagramを一つ置き、同じ関係を複数図へ重複させない。問いに必要な面だけ選ぶ。

| 問い | 図の形式 |
| --- | --- |
| 入口から主要state、分岐、終了、失敗、復旧 | core flow |
| status/run/job/retryの遷移 | state diagram |
| DB/API/file/queue間のpayload | data flow |
| entity/aggregate/related table | domain model |
| 画面とユーザー操作 | UI flow |
| system間の厳密な時系列 | 左から右のsequence風SVG |

時間変化を再生する図は `generate-state-diagram-3d` へ渡し、静的core diagramは残す。状態図だけで別の問いに答えられないときだけ `diagram-design` の契約で補助SVGを作る。

## SVG契約

SVG rootに `xmlns`、明示的な `viewBox`、`role="img"`、空でない `<title>` / `<desc>` を付ける。node/edge/labelをclassまたは `data-*` で識別し、edgeには `trigger [guard] / effect` と根拠を短く示す。矢印はmarker、文字列と属性はXML escape、system fontと埋め込みCSSだけを使う。

外部script、font、image、network、`foreignObject`、event handler属性、HTMLでの実行時diagram変換を埋め込まない。色だけで意味を伝えず、過密なら複数SVGへ分けてMarkdown/HTMLから全て参照する。

## ledger

`91_state_diagram.md` に次を記録する。

- system概要、対象branch、SVG参照、用語集
- actor/componentの責務と入出力、stateの意味・invariant・保存先
- 全transitionのtrigger、guard、before/after、effect、side effect、source anchor
- failure/recovery（残存物、retry可否、idempotency、手動復旧）
- data/interface（producer、consumer、validation、永続化）
- 変更fileの論理group、business ruleと理由、監視点・変更時の注意、最初に読むsource/test
- 省略した図と理由、未確認事項

図の言い換えだけにせず、境界条件、代表case、確認できない部分を分けて書く。preview/dry-run、DB mutation、external sync、verificationなど複数modeがあるときは、mode別traceに分け、内部ledger writeと対象データ変更を区別する。rate limitはentity/API request/process/shared quotaの単位をsourceで確認して書く。

## HTML（条件付き）

`91_state_diagram.html` を作る場合はinline SVGの自己完結desktop HTMLとし、SVGとledgerのnode、edge、label、source anchorを一致させる。外部library、script、font、iframe、networkを使わない。zoom/filterなどのJavaScript、mobile/print/PDF対応は明示依頼時だけ追加する。

## 検証

`references/validator-loop.md` と必要なら `references/mermaid-syntax.md` の契約を適用する。

- XML parserで各SVGをparseし、`xmlns`、`viewBox`、`role`、title、desc、主要node/edgeを確認する。
- 外部resource、script、`foreignObject`、event handlerがないことを確認する。
- Markdown/HTMLのSVG参照先が存在し、evidence inventory、図、ledger、source anchorが一致することを確認する。
- 各transitionにtrigger/guard/effectと根拠がある。欠落は根拠不足として明示する。
- failure/recovery、data/interface、読者への含意がscopeに応じて記録されている。
- HTMLを作った場合だけinline SVGと1440x900でのlabel欠落・重なり・overflowを確認する。

検証失敗は原因を直して最初から再実行する。3回直しても成立しない場合は壊れた図を成果物にせず、ledgerと根拠不足を残して報告する。
