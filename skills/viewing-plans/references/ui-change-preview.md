# UI Change Preview Runbook

このrunbookは、UI変更TaskでRoadmap Viewerの計画本文に出すBefore / After previewをauthoringするための契約である。`viewing-plans`の補助資料であり、HTML route、static gate、browser profileは `@context/html-artifact-contract.md` と `.codex/config/html-surfaces.json` を正本にする。

## 使う場面

新規HTMLでは `data-ui-change="true"` と `script[type="application/json"][data-plan-fragment="ui-preview"]` を同じTaskへ置く。以下のpayloadを、計画を作るLLMが対象sourceに基づき自動で書く。`ui-preview-json`のMarkdown fenceは既存MD入力の互換形式だけに使う。ユーザーへJSON、metadata、source pathの入力を求めない。

- 使う: navigation項目追加、settings toggle追加、sidebar導線追加、listやformの構造変更、新規画面の追加。
- 使わない: behavior-only変更、copyだけの変更、APIやjobだけの変更、source未確認の既存画面、UI変更か不明なTask。
- 迷う場合: UI変更の有無はsourceと仕様を読んで判断する。既存画面のsourceを確認できなければBeforeを補作せず、Task本文や`uncertainty`に「確認できていない」と書く。

## LLM Authoring Flow

UI変更Taskでは、`30_plan.html`を完成させる前に次を行う。

1. 計画開始時のrepository `HEAD`を40桁commit SHAへ解決し、baselineとして保持する。
2. 仕様、変更対象、routeを確認し、対象componentを読む。直接importされ、変更対象の構造や表示labelを持つcomponentと局所styleも必要な範囲だけ読む。
3. JSX / TSX / templateを意味として読み、表示label、group、並び、action、input、明示stateを抽出する。pixel、余白、色、runtime dataは推測しない。
4. 変更対象周辺だけを5 layout / 5 primitiveへ簡略化し、Beforeを作る。実装sourceで確認できたlabelは`observedLabels`へ記録する。
5. 仕様とTaskの実装手順からAfterを作り、追加・変更・削除をstable IDで対応付ける。
6. role、feature flag、responsive、実データなど確定できない点を`uncertainty`へ分離する。
7. HTMLのTaskへ`data-ui-change="true"`と型付きJSON fragmentを1つ書く。behavior-onlyではfalseとしfragmentを作らない。既存MDを読む場合だけ`UI変更: yes/no`とfenceを使う。
8. Roadmapを通常生成し、snapshotの該当previewが`resolved`または理由付き`unverified`であることを確認する。

## Authoring Source

Before、After、uncertaintyを必ず分ける。

- Before: 計画内に記録した40桁commit SHA上の実装sourceを根拠にする。通常生成ではgeneratorがこのSHAを自動利用する。label、並び、存在するstate、role visibilityだけを確認する。
- After: 正本計画の目的、変更対象、実装手順、仕様に明示された未実装案だけを根拠にする。
- uncertainty: role別表示、feature flag、responsive差分、権限差分など、sourceまたは計画から確定できない事項を入れる。

禁止する入力:

- React、Next.js、Storybook、アプリ本体、任意repository codeのbuild・実行。
- JSX / TSX / template ASTから「見た目」を断定すること。
- 生HTML、inline style、CSS selector、script、external URL、画像URL。
- plan本文や変更対象pathから既存UIを推測してBeforeを作ること。

## Block Contract

各Task内の `ui-preview-json` は1ブロックだけ許可する。Task外block、複数block、Task番号不一致、version不一致はinvalidにする。

rootで使えるkey:

- `version`: `1`だけ。
- `taskNumber`: 対象Task見出しから抽出した数値文字列。例えば `## Task 1:` なら `"1"` とし、別Taskへfallbackしない。
- `previews`: 1件以上、最大3件のpreview。

previewで使えるkey:

- `id`: Task内で一意なpreview ID。
- `title`: 本文の変更前後に表示する短い名前。
- `layout`: `topnav`、`sidebar`、`settings`、`list`、`form` のいずれか。これは表示presetであり、item primitiveではない。
- `provenance`: Before / Afterの根拠。
- `before`: base refから確認した現状模型。
- `after`: 計画案の模型。
- `uncertainty`: 未確認事項の配列。

`provenance.before` は `source`、`baseRef`、`observedLabels` を持つ。`source` は `repo:<relative-path>#<anchor-or-Lx-Ly>`、`baseRef` はplan authorが意図したbase ref、`observedLabels` はbase refで実際に確認したラベル配列である。新規画面では `before.items` を空にし、`provenance.before.source` は置かない。

`provenance.after.source` は、Afterの根拠になったplan内の見出し、checkbox、または仕様参照である。Afterは未実装案なので、実装済みsourceとして扱わない。

`baseRef`は40桁の固定commit SHAとする。generatorはplan内に単一のSHAがある場合、CLI指定なしで自動利用する。CLI `--base-ref`を指定した場合はCLIを優先し、plan宣言refと一致しなければならない。複数SHA、mutable ref、ref解決不能、anchor drift、Roadmap Task Hub経由では、Beforeは補作せず`unverified`と理由を返す。

## Items

itemで使えるkey:

- `id`: Before / Afterで同じ要素を対応付けるstable ID。
- `label`: 画面上の短い表示名。
- `kind`: `label`、`item`、`group`、`action`、`input` のいずれか。5 layoutで共通のprimitiveとして使う。
- `change`: `same`、`added`、`modified`、`removed` のいずれか。
- `state`: 任意。enabled、disabled、selected、checked、empty、errorなど、画面上の状態を短く書く。

unknown keyとunknown kindはinvalidにする。値は表示前にescapeされる前提だが、authorはHTMLとして解釈される文字列を書かない。同じ要素は同じ`id`を維持し、順序はitems配列の順番、表示内容は`label`、状態差分は`state`で表す。並び替えのために別IDを作らない。

## Layout Presets

5 layoutは表示presetであり、item kindとは独立している。

- `topnav`: 横並びの主要導線やheader action。
- `sidebar`: 主要導線、group、選択中item。
- `settings`: group、label、input、補助説明。
- `list`: label、item、空状態、action。
- `form`: group、label、input、検証message、action。

## Payload examples

新規HTMLでは各例のJSONを次の形で同じTaskに置く。JSONへ本文を複製しない。

```html
<script type="application/json" data-plan-fragment="ui-preview">
{"version":1,"taskNumber":"1","previews":[...]}
</script>
```

以下のfence表記はpayloadを読みやすく示すもので、新規30_plan.mdを作る指示ではない。

`topnav`:

```ui-preview-json
{"version":1,"taskNumber":"1","previews":[{"id":"app-shell-nav","title":"App shell navigation","layout":"topnav","provenance":{"before":{"source":"repo:app/layout.tsx#L10-L16","baseRef":"0123456789abcdef0123456789abcdef01234567","observedLabels":["Home"]},"after":{"source":"Task 1 実装"}},"before":{"items":[{"id":"nav-home","label":"Home","kind":"item","change":"same"}]},"after":{"items":[{"id":"nav-home","label":"Home","kind":"item","change":"same"},{"id":"nav-reports","label":"Reports","kind":"item","change":"added"}]},"uncertainty":[]}]}
```

`sidebar`:

```ui-preview-json
{"version":1,"taskNumber":"2","previews":[{"id":"project-sidebar","title":"Project sidebar","layout":"sidebar","provenance":{"before":{"source":"repo:src/sidebar.tsx#Overview","baseRef":"0123456789abcdef0123456789abcdef01234567","observedLabels":["Overview"]},"after":{"source":"Task 2 実装"}},"before":{"items":[{"id":"side-overview","label":"Overview","kind":"item","change":"same","state":"selected"}]},"after":{"items":[{"id":"side-overview","label":"Overview","kind":"item","change":"same"},{"id":"side-review","label":"Review","kind":"item","change":"added"}]},"uncertainty":["権限がないroleでReviewを隠すかは未決"]}]}
```

`settings`:

```ui-preview-json
{"version":1,"taskNumber":"3","previews":[{"id":"notification-settings","title":"通知設定","layout":"settings","provenance":{"before":{"source":"repo:app/settings/page.tsx#email","baseRef":"0123456789abcdef0123456789abcdef01234567","observedLabels":["Email alerts"]},"after":{"source":"Task 3 実装"}},"before":{"items":[{"id":"email-toggle","label":"Email alerts","kind":"input","change":"same","state":"checked"}]},"after":{"items":[{"id":"email-toggle","label":"Email alerts","kind":"input","change":"same","state":"checked"},{"id":"weekly-digest","label":"Weekly digest","kind":"input","change":"added","state":"unchecked"}]},"uncertainty":[]}]}
```

`list`:

```ui-preview-json
{"version":1,"taskNumber":"4","previews":[{"id":"invoice-list","title":"Invoices list","layout":"list","provenance":{"before":{"source":"repo:src/invoices/List.tsx#statusHeader","baseRef":"0123456789abcdef0123456789abcdef01234567","observedLabels":["Status"]},"after":{"source":"Task 4 実装"}},"before":{"items":[{"id":"status-label","label":"Status","kind":"label","change":"same"}]},"after":{"items":[{"id":"status-label","label":"Status","kind":"label","change":"same"},{"id":"owner-label","label":"Owner","kind":"label","change":"added"}]},"uncertainty":[]}]}
```

`form`:

```ui-preview-json
{"version":1,"taskNumber":"5","previews":[{"id":"profile-form","title":"Profile form","layout":"form","provenance":{"before":{"source":"repo:src/profile/Form.tsx#name","baseRef":"0123456789abcdef0123456789abcdef01234567","observedLabels":["Name"]},"after":{"source":"Task 5 実装"}},"before":{"items":[{"id":"name-input","label":"Name","kind":"input","change":"same"}]},"after":{"items":[{"id":"name-input","label":"Name","kind":"input","change":"same"},{"id":"team-input","label":"Team","kind":"input","change":"added"}]},"uncertainty":["Teamの候補値sourceは別Taskで決める"]}]}
```

新規画面:

```ui-preview-json
{"version":1,"taskNumber":"6","previews":[{"id":"audit-log-page","title":"Audit log page","layout":"list","provenance":{"before":{"baseRef":"0123456789abcdef0123456789abcdef01234567","observedLabels":[]},"after":{"source":"Task 6 実装"}},"before":{"items":[]},"after":{"items":[{"id":"page-title","label":"Audit log","kind":"label","change":"added"},{"id":"filter-user","label":"User filter","kind":"input","change":"added"},{"id":"export-action","label":"Export","kind":"action","change":"added"}]},"uncertainty":["表示対象event typeは仕様で未確定"]}]}
```

## Omission And Limits

Previewは画面全体ではなく、変更対象周辺の小さなUI模型にする。

- 1 Taskあたり `ui-preview-json` は1ブロック。
- 1 blockあたり最大3 previews。
- 1 sideあたり最大24 item。
- 1 label / state文字列は最大120文字。
- 1 blockは最大16KiB。
- 同一画面の関係ないnav、装飾、画像、実データの長い一覧は省略する。
- 省略したものは「存在しない」と表現せず、必要なら`uncertainty`またはEvidenceに「previewでは省略」と書く。

## New Screens

新規画面ではBeforeの空カードを作らない。`before.items`は空、`provenance.before.source`はなし、`provenance.before.observedLabels`は空にする。表示はAfter-only wireframeと「新規画面」labelにし、Afterにも実装済みと読める文言を置かず、「計画案・未実装」を常時表示する。

## Visual Guidance

reference HTMLから得た指針は、見た目をコピーする材料ではなく、Roadmap内の比較を読みやすくするための制約である。

- 900px程度のeditorial canvasに収まる、短い比較面として考える。
- ページ全体ではなく、topnavやsettings groupなどの小さいUI模型を並べる。
- 新規画面はAfter-onlyで、余白とlabelにより「これから作る画面」だと分かるようにする。
- Google Fonts、外部CSS、外部画像、reference HTMLのtokenはコピーしない。既存Roadmapのdesign token、system font、CSPを維持する。

## Verification Cost

通常のRoadmap生成ではstatic gateとdesktop smokeを実測する。renderer、共通CSS、UI preview common primitive、breakpoint、focus restoration、live updateの共通挙動を変えた場合だけ、manifestにある `roadmap-matrix` 全体を実測する。

`roadmap-matrix` の契約自体は変えない。375px、768px、1440px、200% zoom、forced colors、reduced motion、contrastはrelease / renderer変更のgateとして残す。

browser automationでは、まずoverflow、focus、keyboard、console/page errorなどの決定的assertionを見る。画像またはLLMによるレビューは、browser assertionが失敗したsurface、または人間が視覚判断を明示的に求めたsurfaceだけに限定する。
