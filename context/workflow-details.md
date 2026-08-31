# 条件付きworkflow詳細

通常のPhase手順は context/workflow-rules.md に置き、この文書には発火したときだけ読むgateを置く。詳細schemaは context/memory-file-formats.md、委譲は context/agent-team-routing.md、HTMLの機械契約は context/html-artifact-contract.md と config/html-surfaces.json を参照する。

## Fast Track

次の全条件を満たす低riskの既知手順だけに適用する。

- 変更は1–5 file、100 logical diff LOC以下で、既存patternを使う。
- 新規architecture判断、security / auth、外部write、権限・課金・不可逆操作、runtime policy変更がない。
- safety triggerがfalseで、acceptanceと検証が一回の実行で閉じる。

Phase 0で05_log.mdを作り、Phase 1で対象と影響を確認する。Phase 2では短い計画、acceptance、write scope、Delegation Decisionを記録し、Phase 3で実装、Phase 4でfresh checkと最小の関連checker、Phase 5で変更量を報告する。roadmapの明示要求やGoalの使用がある場合はFast Trackを理由に表示・evidence・承認を省略しない。条件に迷えば通常laneへ戻す。

## Blueprint

依存DAG、Cold-Start Brief、複数PRの設計図が一つのsessionに収まらない場合、Phase 0の前にblueprintを作る。単にsessionを分けるだけなら不要である。

BlueprintはWork Unit（WU）の目的、依存、owned paths、handoffを整理するだけで、各WUのPhase 0–5.5、調査、acceptance、review、commit policyを置き換えない。WUごとにfresh contextを作り、Cold-Start BriefがあればPhase 0で完全一致のsession / threadと照合する。依存が崩れたら実装を止め、planとhandoffを更新する。

## Goal readiness

persistent Goal、/team-run、Goal toolを使うときだけ、Phase 1のevidenceとGO/NO-GOの後にgoal-setterのReadiness checkを読む。outcome、Done、scope、evidenceが観測可能で、baselineと完了条件があることを確認する。改善を主張するGoalはbaselineなしで確定しない。materialな変更は旧Goalを黙って置き換えず、再監査と必要なuser gateへ戻す。

## UI/UX Design Approval

UI、UX、product flow、visual direction、layout、interaction model、主要component patternに新しい判断がある場合は、production UIの最初のwrite前にこのgateを通す。既存の承認済みdesign systemを忠実に実装するだけ、または見た目を変えないbehavior-only bug修正は対象外である。

1. projectの .interface-design/system.md と対象ユーザー、課題、主要画面を確認する。
2. 小規模は意味の異なる2案以上、大規模は原則3案を比較し、tone、layout、color、typography、depth、記憶に残る要素、密度、trade-off、riskを示す。
3. 選択案と承認内容を05_log.mdと30_plan.htmlへ保存し、Phase 2.5へ進む。比較mockupは提案artifactで、production実装の承認とは分ける。
4. 承認後にmaterialなvisual direction、layout、interaction、componentを変える場合は再承認する。

viewing-plansのUI previewはこの承認の代替ではない。source-backed Before、計画上のAfter、uncertaintyを分け、`~/.codex/skills/viewing-plans/references/ui-change-preview.md`のschemaに従う。

## User Validation Gate

外部送信・公開、不可逆な削除や上書き、権限・課金・認証の変更、依頼範囲を実質変更する選択、安全に発見できない重要情報がある場合だけ、ユーザー確認を停止点にする。通常の依頼済みlocal変更では依頼自体を計画・実装の承認と扱い、計画・review・checkpointの作成だけで確認待ちにしない。ユーザーが「調査だけ」「計画だけ」「実装前に確認」と指定した場合、またはUI/UX gateが発火した場合はそこで停止する。Fast TrackでもこのGateの対象なら省略しない。

Phase 2.5のacceptance具体化は確認待ちの理由にならない。追加・削除・意味変更などmaterialな範囲変更が生じたときだけ、このGateを再評価する。

## HTML artifact gate

HTMLを生成、更新、配布、またはMCP Apps resourceとして返す場合は、最初のwrite前にmanifestを確認する。html、design-artifact、html-wireframe、html-prototype、html-plan、html-diagramのいずれか一つをrouteに選び、producer、source、output、static profile、browser profileが登録済みであることを確認する。未登録なら配布せず、manifest・checker・docsを揃える計画へ戻す。

static gateを先に通し、要求されたbrowser profileでviewport、zoom、overflow、keyboard、focus、forced colors、reduced motion、contrast、console / page errorを確認する。warningをPASSの代替にしない。Roadmapは共通syncが既存parserとgeneratorを使ってatomicに生成し、invalid renderで既存成果物を上書きしない。MCP Appsは対応hostのresource contractとtext fallbackを保ち、外部write・公開・deployの承認をこのgateで推測しない。

図の正本はSVGであり、Markdownへ新しいMermaidを生成しない。HTML diagramは正本SVGの派生物として扱い、登録済みprofileを通過させる。

## 計画を深める判断

30_plan.htmlを作った後、追加調査で意思決定が変わる不確実性がある場合だけdeepening-planを使う。小規模、既知手順、追加調査が計画を変えない場合は省略し、理由を05_log.mdへ残す。ADRは rules/adr-criteria.md の3条件を全て満たす判断だけを作る。

## Review escalation

freshな機械検査を先に行い、リスクに合う最小の独立checkerを選ぶ。CRITICAL、正しさに関わるIMPORTANT / MINORを修正し、指摘が残る間は対象を絞って再検証する。権限、外部write、不可逆操作、重要設計は独立reviewまたは人間gateを必須にする。全員固定review、固定round、行数だけのreview数決定はしない。各finding、再起動したrole、skip理由は05_log.mdへ記録する。

詳細なreview matrix、UI preview、HTML static/browser契約は各正本へ戻り、この文書に複製しない。
