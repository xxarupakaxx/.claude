---
name: show-me
description: 現在の話題を、最小限の擬似コード、call tree、component / file tree、ファイル・関数依存trace、diff、またはSVGで視覚的に説明する。ユーザーが「show me」「図で」「構造を見せて」「流れを見せて」「ファイルごとに処理を追いたい」など、文章だけでなく見える形の説明を求めたときに使う。複数章の長文資料や自己完結HTML文書はcreating-html-documentsへ渡す。
---

# Show Me

現在の話題を、要点が最も速く伝わる小さな表現で見せる。前置きは省き、短い説明を視覚表現の近くに置く。根拠にない人物、数値、状態、接続は補わない。

## Ownerを決める

一つの問い、一つのflow、一つのbefore / afterを見せる場合は、このSkillがownerになる。複数の主要主張やsection、source inventory、claim ledger、文書型に沿った章立てが必要な場合、または自己完結HTMLを求められた場合は、`creating-html-documents`へ次のvisual briefを渡す。

```text
visual-question: 読者が図や差分から理解すべき問い
evidence-anchors: file、symbol、test、sourceなどの根拠
recommended-form: tree、diff、SVGなどの候補
must-show: 欠かせないactor、state、branch、境界
omit: 今回は見せない周辺情報
fallback: 同じ意味を読めるtext表現
```

`creating-html-documents`からsection内のvisual判断を依頼された場合は、文書全体を引き取らない。そのsectionの問いに対する最小表現またはvisual briefだけを返し、`creating-html-documents`へ再委譲しない。章立て、claim ledger、overview trigger、HTMLへの配置、CSP、検証、browser表示は文書ownerが保持する。

## 表現を選ぶ

- ロジックやアルゴリズムは擬似コード。
- 実行時の呼び出し順は call tree。
- UI の構造、state、module 境界は component tree。
- file の責務や refactor の形は浅い file tree。
- 既存の形に対する変更点が中心なら `diff`。
- 3つ以上の要素の関係、流れ、境界を空間で読む必要があるなら SVG。
- UI、layout、状態比較、密な概念を一枚で見せる必要があるならSVG。単一fileのHTML文書として組み立てる必要が生じたら`creating-html-documents`へ渡す。

短い表や箇条書きで同じ内容が伝わる場合は図を作らない。Roadmap の task 順、進捗、完了状態は `viewing-plans` に任せる。詳細な技術図が必要なら `diagram-design` の契約を使う。

## 小さな形

ロジック:

```text
on(save)
  if content is unchanged
    return cached result
  write new content
  return fresh result
```

call tree:

```text
submitForm
  createSession
    persistPrompt
    launchAgent
  navigateToSession
```

component tree:

```tsx
<SessionPage> (apps/example/src/routes/session.tsx)
  useSessionEvents()
  <SessionToolbar>
    <RunSkillButton> (packages/ui)
```

file tree:

```text
src/
├── commands/       # parses user actions
├── sessions/       # owns session state
└── transport/      # sends API requests
```

変更の形:

```diff
 submitForm
   createSession
     persistPrompt
+    expandSkillMention
     launchAgent
-  navigateToSession
+  navigateToSession
+    subscribeToEvents
```

ほとんどが新規で、省略すると ownership や順序が隠れる場合は差分ではなくブロック全体を示す。

## ファイルと関数を依存レベルで追う

複数fileをまたぐ処理について「入口からどの関数が何を呼び、どこで副作用が起きるか」を求められた場合は、浅いfile treeだけで終えず、source-backedなdependency traceを作る。

### Levelの定義

Levelは静的import数ではなく、ユーザー操作または外部入力から見た実行時の呼び出し深度とする。入口をLevel 0、その直接の受け手をLevel 1として、DB・外部APIなどの副作用境界まで降りる。循環、callback、queue、workflow再開によって単純な深度にならない場合は、Levelを捏造せずhandoff名または再入点を明記する。

各Levelに最低限、次を結びつける。

- file pathと主要symbol。
- 呼出元と呼出先。
- 受け取るinputと次へ渡すpayload。
- read-only、DB write、外部write、状態遷移などのside effect。
- branch、停止条件、retryまたはrecovery。
- 根拠となるsource anchor。確認できない関係は`unknown`とする。

### modeを混ぜない

同じ入口から複数modeへ分岐する場合は、巨大な一本のtreeにせず、該当するものだけを別traceに分ける。

1. preview / dry-runなどのread-only経路。
2. DB mutation経路。
3. external sync経路。
4. 実行後verification / completion経路。

dry-runが台帳作成などの内部writeを行う場合は「対象データは未変更」と「実行記録は作成」を分けて書く。placeholder、CSV上の表現、DB上の`null`、実際に永続化される値も混同しない。

外部APIを含む場合は、rate limitの単位を正確に書く。例えば「1 entity/秒」と「1 API request/秒」を同一視せず、process-localかsharedか、readにも適用されるか、retryでrequest数が増えるかをsourceから確認する。

### 出力の既定

まず依存Levelの一覧を置き、その後にmode別call treeを置く。関係が3要素以上でshared dependencyや分岐を空間で読む価値がある場合だけ、`diagram-design`のdependency契約でSVGを加える。

```text
Level 0  Screen.tsx
         submit()
           ↓ POST request
Level 1  route.ts
         POST() → validate() → startWorkflow()
           ↓ validated payload
Level 2  workflow.ts
         runWorkflow() → activity()
           ├─ dry-run → preview service       [read]
           ├─ execute → repository transaction [DB write]
           └─ sync → external client           [external write]
```

続けて、必要なmodeだけを展開する。

```text
dry-run
route.POST
└─ workflow
   ├─ validate source
   ├─ calculate projected result
   └─ save preview ledger   [対象データは未変更／台帳はwrite]

execute
route.POST
└─ workflow
   └─ repository.transaction
      ├─ remove old relation
      ├─ add new relation
      └─ save item result    [DB write]
```

自己完結HTMLが必要なら文書ownerを`creating-html-documents`へ渡し、visual briefに次を追加する。

```text
dependency-level-definition: runtime call depth | handoff stages
mode-traces: preview | mutation | external-sync | verification のうち必要なもの
side-effect-boundaries: DB write、external write、ledger-only write
source-resolution: 入力にない種別や対象をどの関数が解決するか
null-and-placeholder: 表示値、照合値、永続値の対応
rate-limit-unit: entity、API request、process、shared quotaのどれか
```

### 合格条件

- 入口から副作用まで、fileとsymbolを交互に辿れる。
- dependency Levelの意味が明記され、静的import深度と混同しない。
- dry-run、mutation、external sync、verificationの境界が読める。
- 「何を変更するか」と「照合にだけ使う値」が区別されている。
- source種別を入力が持たない場合、その解決方法と曖昧時の停止条件がある。
- rate limitの粒度を過大に保証していない。
- 各edgeをsource anchorへ戻せる。推測は事実として描かない。
- SVGを使う場合は`diagram-design`のnode・edge上限と検証gateを通す。

## SVGとHTMLへのhandoff

新しい図はSVGを正本として保存する。`viewBox`、`role="img"`、`aria-labelledby`、空でない`title`と`desc`を持たせ、色だけに意味を持たせない。HTMLが必要な場合は、SVG、短い読み方、テキストfallback、根拠をvisual briefにまとめ、`creating-html-documents`へ渡す。

SVGはsystem fontと埋め込みCSSだけで自己完結させる。外部font、画像、script、iframe、network request、local serverは使わない。製品を説明するときは、実際のlabel、色、spacing、componentを根拠から取る。

完成後に構文、可読性、根拠との対応を確認する。ユーザーが開かないよう指定していなければ、利用中のホストが提供する安全なローカル viewer で検証済みファイルを開く。開けない場合は、失敗理由と絶対 path を返す。

## 密度

現在の問いに必要な call、file、prop、state、boundary だけを残す。複数形式を組み合わせてもよいが、全部は使わない。視覚表現が文章を重複するだけなら削る。
