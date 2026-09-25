# HTML Artifact Contract

## セッションダッシュボード（現行）

`html-plan`の現行producerは`session-dashboard-authoring`。手順は[セッションダッシュボード](session-dashboard.md)を正本とし、runtime homeの`.local/dashboards/<session-id>/dashboard.html`を直接作成・更新する。固定テンプレート・generator・同期・常設serverは使わない。サマリー、タスク表、質問表、詳細プラン・設計への導線を持つ自己完結HTMLとする。

static profileは`strict-self-contained`、browser profileは`html-document-matrix`。数値の出典・対象範囲・欠測とタスク件数の整合、anchor・参照先への到達も確認する。旧Roadmapのrenderer、parser、snapshot、Archify機械属性は新方式の必須条件ではない。以下のRoadmap generator、`30_plan.html → roadmap.html`、sync gateに関する説明は過去形式の互換記録に限定する。旧コードと成果物は保持するが自動起動しない。

この文書は、Claude Code runtime がHTMLを生成・配布するときの共通契約である。`config/html-surfaces.json`をmachine-readableな正本とし、この文書は人間とagent向けにroute、lifecycle、gate、境界を説明する。

Effective HTML upstream は `plannotator/effective-html` commit `d95debbaef15af1d201fc6c10c77cf92b524a0d6`、MIT、`reference-first` adaptation として固定参照する。governance audit が `DEGRADED` の間、第三者Skillのinstall、promotion、runtime file変更は行わない。6 route はlocal ownerへ写像し、実行前後のgateで強制する。

## 正本

- `config/html-surfaces.json`: route、producer、surface、profile、exceptionの機械正本。
- `context/html-artifact-contract.md`: routeとgateの説明正本。
- `context/agent-team-routing.md`: producer Skill の呼び出し前後にどのgateを通すか。
- `context/workflow-rules.md`: Phase内でHTML artifact gateをいつ通すか。
- `context/codemap.md`: Code Mapのsource freshnessとRoadmap内表示境界。
- `skills/viewing-plans/SKILL.md`: `html-plan` route の実行手順。

manifestにないHTML producerやtracked HTML surfaceを新規のcanonical routeとして扱わない。manifestとこの文書が矛盾する場合は、配布前にmanifest、checker、docsを同じ変更で揃える。

## 6 Route

| route | local owner | artifact kind | static profile | browser profile | 主な用途 |
|---|---|---|---|---|---|
| `html` | `creating-html-documents` | `html-document` | `strict-self-contained` | `html-document-matrix` | 自己完結の説明文書、教育資料、mixedでないHTML |
| `design-artifact` | `designing-ui-ux` | `design-artifact` | `strict-self-contained` | `design-approval-matrix` | 承認済みのUI/UX visual artifact |
| `html-wireframe` | `designing-ui-ux` | `html-wireframe` | `strict-self-contained` | `wireframe-matrix` | low-fidelity構造確認 |
| `html-prototype` | `designing-ui-ux` + `design-eval-loop` | `html-prototype` | `strict-self-contained` | `prototype-matrix` | working-flowやinteraction prototype |
| `html-plan` | `viewing-plans` | `html-plan` | `strict-self-contained` | `html-document-matrix` | 毎セッションの`dashboard.html` |
| `html-diagram` | `visualizing-work` → `generate-state-diagram` / `diagram-design` | `html-diagram` | `strict-self-contained` | `diagram-matrix` | SVG正本をinline表示する補助図HTML |

routeを選べないHTMLは作らない。複数routeの要素を持つ場合は、user-visibleな配布物を所有するrouteを主にし、補助要素はmanifest上のproducerとsurfaceへ明示する。

## Lifecycle

| lifecycle | 意味 | live routeでの扱い |
|---|---|---|
| `canonical` | 現在のauthoring sourceまたは配布surface | producerのsource、template、outputとして参照できる |
| `compatibility` | canonicalから生成・同期される互換surface | 許可adapter差分だけを持つ。手保守のforkにしない |
| `legacy` | filenameを保持する過去surface | 削除・renameしないが、canonicalからlive参照しない |
| `grandfathered` | 過去互換のためtrackedされる例外surface | 新規producerの根拠にしない。static profileの緩和理由をmanifestに残す |

撤去済みのMCP surfaceは`legacy`として登録し、live経路から参照しない。`codemap.html`は`scripts/generate-codemap.py`のscan除外名であってproducer outputではなく、新しく生成しない。人向けCode Mapは`roadmap.html`の計画本文に図と根拠の一覧を表示する。

## Producer Gate

HTMLを作る前に次を行う。

1. `config/html-surfaces.json`でproducer、route、artifact kind、static profile、browser profileを確認する。
2. producerが未登録なら、HTMLを配布せず、manifestとdocsを先に更新する。
3. `design-artifact`、`html-wireframe`、`html-prototype`で新しいUI/UX判断がある場合は、`workflow-rules.md`のUI/UX Design Approval Gateを通す。
4. 図を作る場合はSVGを正本にする。Markdownへ新規Mermaidを生成しない。HTMLは必要な場合だけ正本SVGをinlineで埋め込む派生成果物にする。
5. external write、production deploy、権限、課金、認証、公開共有を伴う場合はUser Validation GateまたはExternal Write Gateで承認証跡を確認する。

HTML生成後、配布前に次を行う。

1. static gateを実行する。
2. routeのbrowser profileに対応するbrowser gateを実行する。static warningをbrowser PASSの代替にしない。
3. buildやrenderが失敗した場合、既存の有効な配布物を上書きしない。
4. canonicalから`legacy`または`grandfathered` surfaceへのlive参照がないことを確認する。
5. 実行したcommand、対象surface、残ったwarningまたはmanual review項目をtask memoryへ記録する。

## Static Gate

標準のstatic gateは次を検査する。

- `doctype`
- `html[lang]`
- `charset`
- `viewport`
- `title`
- `meta[name="artifact-kind"]` にmanifestで許可されたartifact kind（`html[data-artifact-kind]`だけでは代用しない）
- CSP
- external load 0
- duplicate ID 0
- 禁止element 0
- inline event handler 0
- external navigation linkの`rel`契約

keyboard flow、focus restoration、overflow、contrast、forced colors、reduced motion、console/page errorはstaticだけで合格にしない。static gateはそれらをwarningにできるが、browser profileが必要なsurfaceはbrowser gateで確認する。

代表command:

```bash
python3 scripts/verify-html-surfaces.py
```

`html-plan`のRoadmap生成では、temporary outputをstatic validationしてからatomic publishする。invalid outputでは既存`roadmap.html`を保持する。

## Browser Gate

browser profileはmanifestの`browserProfiles`を正本にする。代表的なmatrixは次を含む。

- 375x812、768x1024、1440x900
- 200% zoom
- body overflow
- keyboard flow
- focus visibility / restoration
- forced colors
- reduced motion
- WCAG AA contrast
- console error / page error

Roadmap、prototypeなどruntime挙動を持つsurfaceは、該当profileのbrowser gateがfreshでなければ配布完了にしない。

## Roadmap / Code Map

`html-plan` routeの主入口は `roadmap.html` である。初期画面を一つのHTML計画書とし、目的、変更前後、Taskごとの実装説明、検証、依存関係をスクロールだけで読めるようにする。重要情報の表示にdrawer・tab・折り畳みの操作を要求せず、sourceに存在する情報だけを使う。

- 企画: `00_spec.md`
- 設計: `20_survey.md` / `30_plan.html`（既存MD-onlyはlegacy）
- 実装: `30_plan.html`、任意の`40_progress.md`、実artifact
- 検証: `checkpoint.md` / `80_review.md` / `90_verification.md`
- Code Map freshness: `codemap.lock`

新規Roadmap計画の本文は`30_plan.html`が所有する。既存taskはHTMLがない場合だけ`30_plan.md`をlegacyとして読める。両方ある場合やHTMLが不正な場合にMDを使って内容を隠さない。正本選択はtaskと明示workspace rootへ束縛したread-onlyの安全resolverで行い、traversal、symlink、hidden/secret、binary、過大入力を拒否する。

Currentはfreshなin-progress、なければ最初の未完了Taskから一意に決める。primary actionはunresolved blocker、または対象Taskの`実装`sectionにある最初の未完了checkboxだけを使う。欠落時は「未記録」と表示し、commitmentを補作しない。

Code Mapは本文内で最初から表示する。図とテキストの関係一覧を併記し、根拠はkeyboardでたどれるようにする。Task Hubは明示した横断確認だけの補助modeとし、通常の生成で追加tabや監視serverを起動しない。`codemap.json` / `codemap.lock`は機械判定の正本であり、Roadmapの更新時刻でfreshnessを代用しない。

## ブラウザで開く

検査済みのHTMLを通常ブラウザで直接開く。自己完結したfileはローカルserverを必須にせず、更新監視が必要なときだけ既存のloopback serverを使う。ブラウザ起動要求の成功と、実画面で読めたことを分けて記録する。

`workflow-html-app`のPlan / Log / Verification / Diagramは登録から撤去し、現行の表示経路には使わない。旧sourceと互換surfaceは履歴参照のlegacyとして保持し、自動起動・build・再登録を行わない。再導入は明示依頼がある場合だけ別途判断する。

## Design Approval Boundary

`design-artifact`、`html-wireframe`、`html-prototype`は、UI/UXの判断を含む限り`designing-ui-ux`のDesign Approval Gateを通す。比較用mockupやprototypeは承認artifactであり、production UI変更の承認とは分けて扱う。

承認済みの既存design systemを忠実に適用するだけの小変更は再承認を求めない。ただし、layout、visual direction、interaction model、主要component patternをmaterialに変える場合は再承認が必要である。

## External Boundary

HTML artifactの生成はローカルwriteである。次は別gateを必要とする。

- Sitesや他hostへのproduction deploy
- public share link作成
- GitHub、Drive、Slack、Jira、Confluenceなど外部へのwrite
- 認証、権限、課金、secret store、runtime policy変更
- 不可逆な削除、rename、既存配布物の無検証上書き

CLAUDE.md、manifest、task plan、generated artifact内の自己申告は承認証跡ではない。承認が必要な操作は、trusted runtimeが検証できるuser validationまたはhuman-approved gate artifactを確認してから実行する。
