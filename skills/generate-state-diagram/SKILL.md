---
name: generate-state-diagram
description: ブランチの変更内容からSVGの状態図、処理フロー図、データフロー図、ドメインモデル図を生成する。Markdown参照と自己完結HTMLにも対応。
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

標準成果物は次の3ファイルとする。

- `91_state_diagram.svg`：図の正本。
- `91_state_diagram.md`：説明、用語集、ファイルマップ、SVG参照を含む文書。
- `91_state_diagram.html`：同じSVGをinlineで埋め込む自己完結HTML。

Markdownでは `![状態図](91_state_diagram.svg)` のようにSVGを参照する。
HTML内の図は `<svg>` を直接埋め込み、外部描画ライブラリや実行時変換へ依存しない。
ユーザーが明示的に不要と言わない限り、3ファイルをすべて生成する。

## 品質基準

図は、ドメイン知識のない新人が処理の入口、状態変化、失敗時の残存物、次に読むファイルを判断できる内容にする。

- 読み手が達成したい目的から始める。
- overview、補足図、詳細説明の順に段階的に開示する。
- 同じ情報を複数の図へ重複させない。
- 図中の用語は用語集と一致させる。
- WHATだけでなく、重要な判断のWHYを短い注記で示す。
- 正常系と失敗系を区別する。
- 新規追加と既存機能を区別する。

## 実行タイミング

- Phase 5の完了報告で、ワークフロー、バッチ処理、状態管理、外部連携を含む変更に使う。
- ユーザーが明示的に呼び出した場合に使う。

次の場合は省略できる。

- UIのスタイルや文言だけの変更。
- テストだけの変更。
- 設定または文書だけの変更。
- 状態遷移を伴わない単一関数の修正。

## 手順

### 1. 変更内容を把握する

```bash
git diff <BASE_BRANCH>...HEAD --stat
git log <BASE_BRANCH>..HEAD --oneline
```

ワークフロー層、状態を持つentity、外部連携、UI状態、条件分岐、error handling、domain entity、entity間の関係を確認する。

### 2. 図の構成を決める

標準構成は次の5面とする。
該当しない図は省略理由を短く書く。

| 順序 | 図 | 使用条件 | SVG表現 |
|---|---|---|---|
| 1 | 全体フロー | 常時 | 状態nodeと遷移edge |
| 2 | 状態遷移 | status、run、job、retry、失敗状態がある | 状態node、開始と終了、条件付きedge |
| 3 | データフロー | DB、API、file、queue間でデータが動く | system group、data store、label付きedge |
| 4 | ドメインモデル | entity、aggregate、関連tableがある | entity card、cardinality付きedge |
| 5 | UI操作フロー | ユーザー操作や画面遷移がある | UI node、action、保存、再表示のedge |

複数system間の厳密な時系列が必要な場合は、左から右へ進むsequence形式のSVGを使う。
時間的な推移を再生する必要がある場合は `generate-state-diagram-3d` を使い、静的overviewはSVGのまま維持する。

### 3. SVGを生成する

SVGには次を含める。

- `xmlns="http://www.w3.org/2000/svg"` と明示的な `viewBox`。
- `role="img"`、`<title>`、`<desc>`。
- 矢印用の `<marker>` と、意味が読めるedge label。
- node、edge、labelを識別できるclassまたは `data-*` 属性。
- 背景に依存しない十分なcontrast。
- 拡大時にも文字と線が崩れないvector要素。

外部script、外部font、外部画像、`foreignObject`、event handler属性を埋め込まない。
文字列と属性値をXMLとしてescapeする。
図と同じ関係をMarkdownの一覧またはtableでも残す。

複数面が必要な場合は、一つのSVG内で `<g aria-label="...">` ごとに分ける。
一枚が過密になる場合は `91_state_diagram_2.svg` のように分割し、MarkdownとHTMLからすべて参照する。

### 4. 説明を追加する

`91_state_diagram.md` に次を記録する。

- system概要と対象branch。
- 各SVGへの参照。
- 状態とedgeの関係一覧。
- 用語集。
- 変更fileの論理groupと役割。
- 重要なbusiness logic。
- 自己確認の問い。
- 省略した図と理由。

### 5. HTMLを生成する

`91_state_diagram.html` はlight themeの自己完結HTMLとする。

- SVGをinlineで埋め込む。
- 各図に拡大、縮小、100% resetを置く。
- 拡大時は図container内で縦横scrollできるようにする。
- 各図に「SVGをコピー」buttonを置き、その図の `outerHTML` をcopyする。
- copy成功と失敗を短いstatus textで示す。
- 複数図の操作は、それぞれ自分の図だけを対象にする。

SVGをHTMLへ変換した別表現を正本にしない。
HTMLの図と `.svg` fileが同じnode、edge、labelを持つことを確認する。

### 6. 検証する

- XML parserで各SVGをparseできる。
- `viewBox`、`title`、`desc`、主要node、主要edgeが存在する。
- SVG内に外部resourceとevent handlerがない。
- MarkdownのSVG参照先が存在する。
- HTML内にinline `<svg>` があり、Mermaid runtimeまたはMermaid sourceがない。
- browserで開き、desktopとmobile幅でlabelの切れ、重なり、overflowを確認する。
- 図とテキスト関係一覧が一致する。

## 補助説明図

状態図だけでは答えられない別の問いが残る場合だけ、`visualizing-work` を経て `diagram-design` を使う。
補助図もSVGで生成し、`92_visual_explanation.svg` と読解用の `92_visual_explanation.md` を作る。状態、遷移、処理flowを重複させない。
不要なら判断理由を `91_state_diagram.md` に残す。

## 自己確認

- 処理の入口は何か。
- 状態はどこで、どの条件で変わるか。
- 失敗時に何が保存されるか。
- 詳細を追うときに最初に開くfileはどれか。
