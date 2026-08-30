# Agent Team Routing

ClaudeがSkill、plugin、Agent()、Workflowを選ぶroutingの正本である。Phaseの順序は context/workflow-rules.md、条件付きgateは context/workflow-details.md、artifact形式は context/memory-file-formats.md、modelは rules/model-routing.md、Team Runは context/team-run.md を参照する。projectのAGENTS.md / CLAUDE.mdは追加制約として優先する。

## 責務境界と既定

Claude leadは要件、route、統合、一次資料確認、fresh検証、最終判断、commit / push、外部writeを保持する。Pluginはsourceとdomain preflight、Skillは現在Phaseのdiscipline、Agent()は境界を切った作業、Workflowは依存が明確なpipelineを担当する。pluginがあることだけを理由にAgent()を起動しない。

local Read / Grep / Glob / Bashを先に行い、最小routeを選ぶ。大きなflow、固定全員review、件数合わせのAgent()は既定にしない。user-invokedのSkill / commandは明示要求または既存の承認済み依頼が対象のときだけ起動し、通常のroute選択で自動起動しない。ユーザーが指定したSkillはSKILL.mdを全文確認する。第三者Skillの発見・評判・導入・更新・廃止は skill-governance を入口にし、自動promotionや無審査updateを行わない。

## Delegation Gate

Agent()、Workflow、reviewerを起動する前に全条件を評価する。

| 条件 | PASS |
|---|---|
| Local-first | leadがscopeと既存patternを確認し、一操作では閉じない |
| 並列利益 | 速度、専門性、隔離、または独立証拠の利益が統合コストを上回る |
| 独立証拠 | objective、acceptance、成果物またはcheckerを独立に定義できる |
| Write scope | writerごとのowned_pathsがdisjoint、または対象ごとにwriterを一人に固定できる |
| 外部副作用 | 外部writeがない、または対象・操作・承認が確定している |

同一fileの密結合作業、逐次依存、低価値要約はleadが行う。Gateを満たす非自明な実装だけをAgent()へ渡し、capability不在ならleadが逐次実行して理由を記録する。makerはEvidence Bundle draft、checkerはreview sectionを担当し、makerが最終判定を兼ねない。

### Delegation Decision

route、実装単位、acceptance、write scopeを決めた直後、対象成果物の最初のwriteより前に05_log.mdへDecisionを保存する。decision_unit、gate、passed_conditions、failed_conditions、local_first_evidence、reason、write_scope、acceptance、lead_retainsを含める。material change後はsupersedesを付けて再評価する。

Work Packetには objective、scope、out_of_scope、owned_paths、acceptance_ids、constraints、capability_class、safety_decision_id、side_effects_requested、external_write_targets、approval_required、approval_evidence、dry_run_required、baseline、reality_contract、verification、dependencies、handoff_requirements、reviewer_focus、journey_scenarios、negative_paths、completion_targetを含め、該当しない現実条件はN/A: <理由>とする。

## Context BoundaryとJIT brief

grilling / alignmentは未決事項の確認だけを行い、ここで実装・外部投稿を始めない。spec / handoffは確認済みの合意だけを保存する。実装Agent()へは会話全文でなく、目的、次の未完了Task、対象、依存、検証、決定、不明点、source refsから成るJIT briefだけを渡す。secret、認証済みsession、全tool outputを渡さない。

task-contextは`~/.codex/scripts/task-context.py`を明示root・指定task付きで呼び、引数・出力schemaはcontext helperの実装とtestを正本とする。このroutingで新schemaを捏造せず、list / brief helperはread-onlyに限定する。

## Route選択

| 状況 | route | 境界 |
|---|---|---|
| 既知の小さな実装 | direct lane / implement | acceptanceとfresh検証で閉じる |
| routeが未知の大規模作業 | wayfinder / mapping-large-projects | decision map後にspecまたは実装へ渡す |
| 合意済み要件をspecへ残す | to-spec / writing-specifications | tracker公開は別gate |
| Approved specをsliceへ分ける | to-tickets / creating-tracer-tickets | writerとblocking edgeを固定する |
| 依存DAGやCold-Start Briefが必要 | blueprint | 各WUのPhase 0–5.5を省略しない |
| 複数turnのGoal・Team Journal・Review Heatが有効 | team-run | user-invoked overlay |
| 固定順の専門chainが必要 | orchestrate | 外部副作用は別gate |
| UI/UXの新しい判断 | designing-ui-ux | UI/HTML gateを先に通す |
| 固定点からの差分レビュー | reviewing-code | Phase 4の判定を置き換えない |

canonical入口は `wayfinder`、`to-spec`、`to-tickets`、`implement`、`teach`で、実行規律は対応する実装Skillへ委譲する。`batch-grill-me` と `to-questionnaire` は明示起動時だけのin-progress入口である。retired skill nameを既定routeへ戻さない。

### Delivery lifecycle routing

Workflow routeとLocal / Fast / Standard / Heavy / Judgmentのcapability classは別軸である。fast-track、prd-flow、multi-packet-flowのWork Packet条件はmemory形式とworkflowを正本とする。必要model不在はROUTING_BLOCKED、承認なしの外部writeやruntime policy変更はWAITING_HUMANで停止する。completion_targetとcompletion_stateはmemory形式に従う。

## Skill、HTML、共通sync

調査不足ならresearch / iterative-retrieval、実装ならimplement / tdd / diagnosing-bugs、検証ならverification-loop / reviewing-codeを必要な分だけ読む。team-runは複数turnの共有状態と独立検証が実効的な場合だけ、graph-engineeringは複数loop・typed state・異なるauthorityが必要な場合だけ使う。

HTMLを生成・更新・配布する場合は context/html-artifact-contract.md と config/html-surfaces.jsonを確認し、登録済みproducerだけを使う。Roadmapは30_plan.mdを入力に`~/.codex/scripts/sync-roadmap.py`が検査・生成・atomic publishし、HTMLを手編集しない。図の正本はSVGで、MarkdownへMermaidを生成しない。

ClaudeのRoadmap同期は ~/.codex の共有CLIを明示入口にする。phase 2、3、4、5で同じTASK、run、rootを使い、--dry-runはread-onlyとする。CLI不存在、引数不正、sync失敗時は旧generatorや別CLIへfallbackしない。完了表示はsync PASSとfresh検証の後だけにする。

## 改善候補とExternal Write Gate

失敗や改善案は候補→trial（回帰検査と外部feedback）→adoptの順に扱う。adoptにはowner、承認、rollback、review dateを付け、外部feedbackなしの自動policy promotionやSkill / hook / contextの自動更新をしない。measured tokens、measured bytes、proxy（行数、呼び出し数、概算token）は別記録にする。

issue、PR、comment、label、Slack、Calendar、Drive、deploy、secret store、public share、git pushは対象・差分・principal・承認証跡を確定してからleadが行う。commitも検証成功後にproject policyへ従う。Agent() / Workflowへsecret、secret reference、認証済みsessionを渡さず、権限errorやcontext不一致を別principalへ自動切替しない。既存の承認済み依頼の範囲は、通常routeより優先して維持する。

文案作成を委譲する場合は`~/.codex/scripts/draft_delivery_message.py`経由のtoolなしFast workerを、ephemeral・read-only sandbox・user config無効・shell / browser / apps / multi-agent無効で起動する。Fast workerは文案とclaim_referencesだけを返し、Git/GitHub tool、approval、commit、push、PR作成を持たない。leadがtrusted snapshotとEvidenceを検証してからexternal writeを行う。小さな定型文はlocal templateを優先する。

## Fallback

Skill、plugin、Agent()、Workflow、共通CLIが使えないときは存在を捏造せず、lead逐次実行またはlocal fallbackへ戻し、同じacceptance・安全境界・fresh検証を維持する。主経路の失敗を旧generatorで隠さない。routingの詳細は対象Skill、project正本、workflow-detailsへ戻る。
