---
name: generate-state-diagram
description: ブランチや既存systemから、trigger、guard、状態変化、side effect、failure、recovery、source根拠まで追跡できるSVG状態図・処理フロー図を生成する。「状態図生成」「処理フロー図」「全体像だけでなく詳細も知りたい」等の依頼に使う。必要時だけdesktop向け自己完結HTMLも作る。
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

# ブランチ状態図と処理フロー図の生成

## 出力契約

新しく生成する図はSVGを正本とし、Mermaidを生成しない。

標準成果物は次の2ファイルとする。

- `91_state_diagram.svg`：図の正本。
- `91_state_diagram.md`：詳細ledger、用語、source map、SVG参照を含む読解の正本。

Markdownでは `![状態図](91_state_diagram.svg)` のようにSVGを参照する。
`91_state_diagram.html` は、ユーザーがHTMLまたはbrowser表示を求めた場合、あるいは図と詳細ledgerを同じ画面で読む必要がある場合だけ作る。HTML内の図は `<svg>` を直接埋め込み、外部描画libraryや実行時変換へ依存しない。

PDF、PNG、mobile版、印刷版は標準成果物に含めない。明示依頼がある場合だけ別gateで作る。

## 品質基準

図は、domain知識のない新人が「何が起点で、どの条件で分岐し、何を変更し、失敗時に何が残り、どう復旧し、どのsourceを読めば確認できるか」を判断できる内容にする。

- 読み手が達成したい目的から始める。
- overviewは詳細への索引として使い、説明の代わりにしない。
- 同じ情報を複数の図へ重複させない。
- 図中の用語は用語集と一致させる。
- WHATだけでなく、trigger、guard、effect、WHYを示す。
- 正常系と失敗系を区別する。
- 新規追加と既存機能を区別する。
- sourceで確認できない関係は推測で埋めず、`未確認` と理由を示す。
- 「処理する」「連携する」「更新する」だけのnodeやedgeを作らない。主体、対象、条件、結果を具体化する。

## 実行タイミング

- Phase 5の完了報告で、ワークフロー、バッチ処理、状態管理、外部連携を含む変更に使う。
- ユーザーが明示的に呼び出した場合に使う。

次の場合は省略できる。

- UIのスタイルや文言だけの変更。
- テストだけの変更。
- 設定または文書だけの変更。
- 状態遷移を伴わない単一関数の修正。

## 手順

### 1. sourceと問いを固定する

```bash
git diff <BASE_BRANCH>...HEAD --stat
git log <BASE_BRANCH>..HEAD --oneline
```

branch差分だけでなく、caller、callee、data model、test、設定、運用入口まで読む。読者が図を見て答えたい問いを1〜3件に絞る。

### 2. evidence inventoryを作る

描画前に、次をcompactな作業表へ抽出する。該当しないfieldは `N/A`、sourceで確認できないものは `未確認` とする。

| 対象 | 必須情報 |
|---|---|
| actor / component | 責務、入力、出力、所有するstate、source anchor |
| state | 意味、invariant、保存場所、開始条件、終了条件 |
| transition | trigger、guard、before、after、effect、side effect、failure、recovery、source anchor |
| data / interface | fieldまたはpayload、producer、consumer、validation、永続化 |
| external boundary | 呼び出し先、timeout、retry、idempotency、partial failure |

source anchorは可能な限り `path:line`、symbol、test名で示す。抽出表に根拠がないedgeは描かない。

### 3. 図の構成を決める

標準は、一つのcore diagramと詳細ledgerである。図面数を増やして情報量を水増ししない。追加面は、core diagramとledgerでは別の読者の問いに答えられない場合だけ作る。

| 順序 | 図 | 使用条件 | SVG表現 |
|---|---|---|---|
| 1 | core flow | 常時 | 入口、主要state、分岐、終了、失敗と復旧 |
| 2 | 状態遷移 | status、run、job、retry、失敗状態がある | 状態node、開始と終了、条件付きedge |
| 3 | データフロー | DB、API、file、queue間でデータが動く | system group、data store、label付きedge |
| 4 | ドメインモデル | entity、aggregate、関連tableがある | entity card、cardinality付きedge |
| 5 | UI操作フロー | ユーザー操作や画面遷移がある | UI node、action、保存、再表示のedge |

複数system間の厳密な時系列が必要な場合は、左から右へ進むsequence形式のSVGを使う。
時間的な推移を再生する必要がある場合は `generate-state-diagram-3d` を使い、静的core diagramはSVGのまま維持する。

### 4. SVGを生成する

SVGには次を含める。

- `xmlns="http://www.w3.org/2000/svg"` と明示的な `viewBox`。
- `role="img"`、`<title>`、`<desc>`。
- 矢印用の `<marker>` と、意味が読めるedge label。
- edge labelには、可能な範囲で `trigger [guard] / effect` を短く示す。
- node、edge、labelを識別できるclassまたは `data-*` 属性。
- 背景に依存しない十分なcontrast。
- 拡大時にも文字と線が崩れないvector要素。

外部script、外部font、外部画像、`foreignObject`、event handler属性を埋め込まない。
文字列と属性値をXMLとしてescapeする。
図と同じ関係をMarkdownの遷移ledgerでも残す。SVGだけで詳細を完結させようとして文字を詰め込まない。

複数面が必要な場合は、一つのSVG内で `<g aria-label="...">` ごとに分ける。
一枚が過密になる場合は `91_state_diagram_2.svg` のように分割し、MarkdownとHTMLからすべて参照する。

### 5. 詳細ledgerを書く

`91_state_diagram.md` に次を記録する。

- system概要と対象branch。
- 各SVGへの参照。
- actor / componentの責務と入出力。
- 状態の意味、invariant、保存場所。
- 全遷移のtrigger、guard、before / after、effect、side effect、source anchor。
- failure / recovery matrix。失敗時の残存物、retry可否、idempotency、手動復旧を含む。
- data / interface contract。producer、consumer、validation、永続化を含む。
- 用語集。
- 変更fileまたは主要sourceの論理groupと役割。
- business ruleと、そのruleが必要な理由。
- 読者への含意。監視点、変更時の注意、最初に読むsourceを具体化する。
- 省略した図と理由。

単なる見出し一覧や図の言い換えにしない。重要な項目には具体例または代表caseを一つ以上付け、境界条件がある場合は反例も示す。

### 6. 必要な場合だけHTMLを生成する

`91_state_diagram.html` はdesktop向けlight themeの自己完結HTMLとする。

- SVGをinlineで埋め込む。
- 図と詳細ledgerを同じ名称とsource anchorで接続する。
- 図containerはdesktop幅で必要な場合だけ縦横scrollを許可する。
- static HTMLを既定とし、zoom control、copy button、client-side filterなどのJavaScriptを自動追加しない。browser標準のzoomで読む。
- 1440x900を既定確認幅とする。mobile responsive、print stylesheet、PDF exportは明示依頼がない限り作らない。

SVGをHTMLへ変換した別表現を正本にしない。
HTMLの図と `.svg` fileが同じnode、edge、labelを持つことを確認する。

### 7. 検証する

- XML parserで各SVGをparseできる。
- `viewBox`、`title`、`desc`、主要node、主要edgeが存在する。
- SVG内に外部resourceとevent handlerがない。
- MarkdownのSVG参照先が存在する。
- evidence inventoryの確認済み遷移がSVGとledgerに存在し、未確認事項が確認済みとして描かれていない。
- 各遷移にtrigger、guard、effect、source anchorのいずれかが欠ける場合、欠落理由が明示されている。
- failure / recovery、data / interface、読者への含意が対象scopeに応じて記載されている。
- HTMLを作った場合、inline `<svg>` があり、Mermaid runtimeまたはMermaid sourceがない。
- HTMLを作った場合、1440x900でlabelの切れ、重なり、意図しないoverflowを確認する。
- 図、遷移ledger、source anchorが一致する。

## 補助説明図

状態図だけでは答えられない別の問いが残る場合だけ、`visualizing-work` を経て `diagram-design` を使う。
補助図もSVGで生成し、`92_visual_explanation.svg` と読解用の `92_visual_explanation.md` を作る。状態、遷移、処理flowを重複させない。
不要なら判断理由を `91_state_diagram.md` に残す。

## 自己確認

- 処理の入口は何か。
- 各edgeは何をtriggerに、どのguardを通り、何を変えるか。
- 失敗時に何が残り、retryや手動復旧はどう行うか。
- dataは誰が作り、誰が検証し、どこへ保存するか。
- その仕組みが読者の実装・運用判断へどう影響するか。
- 詳細を追うときに最初に開くsourceとtestはどれか。
