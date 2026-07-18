# Agent Team Routing

Claude が plugin、skill、`Agent()`、`Workflow` を選ぶための routing SSoT。

- Phase 順序と品質 gate は `context/workflow-rules.md` を優先する。
- model 選択は `rules/model-routing.md` を優先する。
- `/team-run` のチーム構成・Review Heat・終了判定は `context/team-run.md` を優先する。
- project の `AGENTS.md` / `CLAUDE.md` と project 固有設定は、この global routing より優先する。
- route の入口は `skills/ask-skill-router/SKILL.md` とする。

## 責務境界

| 構成要素 | 所有する責務 | 所有しない責務 |
|---|---|---|
| Plugin | 接続済み source、domain workflow、plugin 固有 preflight | global Phase、delegation の要否、外部書き込みの包括承認 |
| Skill | 現在の Phase 内で使う focused discipline | Phase 0-5.5 全体、project の review / commit policy |
| `Agent()` | 境界を切った調査、実装、独立 review | lead の最終判断、暗黙の権限拡張 |
| `Workflow` | 依存が明確な fan-out、pipeline、結果集約 | 曖昧な仕様判断、外部副作用の承認 |
| Claude lead | route 選択、統合、検証、ユーザーへの説明 | project rule を越えた自律的な権限拡張 |

Plugin が適用されても、それだけで `Agent()` を起動しない。plugin router がある場合は focused skill より先に読み、その preflight と completion gate を守る。

## Delegation Gate

`Agent()` へ委任する前に、次の条件をすべて確認する。満たさない条件があれば Claude lead が逐次実行する。

| 条件 | PASS の基準 |
|---|---|
| Local-first | `Read` / `Grep` / `Glob` / `Bash` または小さな `Workflow` だけでは不足する |
| 並列利益 | 独立作業の速度・専門性の利益が、委任と統合のコストを上回る |
| 独立証拠 | objective、acceptance、成果物または checker を lead から独立して定義できる |
| Write scope | maker ごとの write scope が disjoint、または同じ対象の writer が一人に固定される |
| 外部副作用 | 外部書き込みがない、または対象と操作が既存 project policy かユーザー承認で許可されている |

同一ファイルの密結合作業、逐次依存、低価値な要約は fan-out しない。reviewer は maker の自己申告ではなく、成果物と fresh な検証証拠を見る。

## Context Boundary

- **Alignment**: `grill-me` / `grilling` は、人間の選好と未決事項を一問ずつ明らかにする。ここでは実装・文書更新を始めない。
- **Durable artifact**: `grilling-with-docs`、`writing-specifications`、`handing-off-context` は、確認済みの合意だけを保存する。保存先と外部公開は別 gate である。
- **Fresh implementation context**: route と acceptance が確定した実装単位は、必要な artifact の抽出だけを持って開始する。会話全文や未決の仮説を丸ごと引き継がない。

`mapping-large-projects` は route が霧に包まれた大規模 effort の decision map であり、`team-run` は route と acceptance が既知で、共有状態と独立検証が価値を生む実行協調である。

## Research Ticket Gate

AFK research ticket は facts を集めるためだけに使う。
local-first の後、Delegation Gate をすべて満たす独立調査だけを `Agent()` または `Workflow` に委任し、source link と不確実性を持つ asset を lead に返す。
claim、tracker 作成、comment、label、close は External Write Gate を通す。

## Engineering Lanes

ここに載せるのは shared route として採用した promoted skill と既存の canonical flow だけである。

Matt Pocock skill の全件判定はfixed revisionごとの監査artifactで管理する。
このroutingには41件の詳細を複製せず、運用カテゴリと入口だけを置く。

- **canonical**：`ask-skill-router`、`grilling`、`grilling-with-docs`、`mapping-large-projects`、`writing-specifications`、`creating-tracer-tickets`、`implementing-work`、`tdd`、`diagnosing-bugs`、`reviewing-code`、`modeling-domains`、`designing-codebases`、`handing-off-context`。
- **optional**：`prototyping-solutions`、`improving-codebase-architecture`、`setting-up-engineering-skills`、writing 系、setup 系、niche migration 系。明示依頼または対象repo条件がそろう場合だけ使う。
- **compat/reference**：`choosing-skills` などの旧名やClaude専用補助。入口は既存canonical routeへ寄せる。
- **retired/rejected**：deprecatedな `conducting-quality-assurance`、`planning-refactors`、`ubiquitous-language`、Claude専用handoff、in-progressの `batch-grill-me`、`to-questionnaire` は shared engineering lane として推奨しない。

`teaching-concepts` は post-stabilization の教育laneである。
通常の設計、実装、状態図生成では、読者に教えるための原則だけを使い、teaching workspace は明示された教育タスクでだけ作る。

### Engineering Flow Shape

これは route の条件分岐であり、Phase 順序の第二の正本ではない。

- route が見えない巨大案件だけ `mapping-large-projects` を situational on-ramp として使い、判断がそろった後に `writing-specifications` または直接 `implementing-work` へ渡す。
- route が明確で、単一 session に収まり direct requirement と acceptance criterion で検証できる作業は、spec と ticket を省略して `implementing-work` へ進める。この分岐を `direct lane` と呼ぶ。
- 複数 session に分ける作業は durable spec または handoff artifact を残し、実行単位をtracker化する場合だけ `creating-tracer-tickets` を使う。各実装単位は durable artifact から fresh context で始める。
- route が明確な大規模作業を WU と依存へ分ける場合は `blueprint` を使い、fog-of-war の探索と混同しない。

これらの skill は user-invoked である。
ある route の完了は次 route の提案条件を満たすだけで、後続 skill の自動実行、tracker 公開、commit、push を許可しない。

| 条件付きlane | 使う条件 | 次の判断 |
|---|---|---|
| `mapping-large-projects` → `writing-specifications` | 目的地はあるがrouteが不明で、decision map後も durable spec が必要 | 未決事項が残るなら alignment に戻す |
| `writing-specifications` → `creating-tracer-tickets` | 承認済みspecを複数の垂直sliceへ分ける必要がある | tracker公開は別承認 |
| `creating-tracer-tickets` → `implementing-work` | ticket単位で acceptance と frontier が明確 | fresh context だけを渡して実装する |
| direct requirement → `implementing-work` | 単一sessionで検証でき、specやticketが過剰 | `tdd`、`diagnosing-bugs`、reviewを必要な分だけ重ねる |

| Signal | Primary route | 起動権 | 境界 |
|---|---|---|---|
| 要件が曖昧で codebase または状態付き docs がある | `grilling-with-docs` | user-invoked | 同じ文脈で alignment を進める。codebase がない場合は `grill-me`。次 route は規模と不確実性で選ぶ |
| 目的地はあるが route がまだ分からない巨大案件 | `mapping-large-projects` | user-invoked | decision map を作る situational on-ramp。route が明確なら spec または直接実装を提案し、tracker 書き込みは別 gate とする |
| route が明確な大規模作業で、依存DAG、Cold-Start Brief、または複数PRの設計図が必要 | `blueprint` | user-invoked | WU と依存を設計する。通常の複数session分割や未知routeの探索には使わない |
| 会話だけでは決められない一つの design question | `prototyping-solutions` | model-invoked | decision evidence を作る。production 実装ではなく、branch / issue / commit は別 gate |
| material な未決事項がない会話を durable spec にする | `writing-specifications` | user-invoked | tracker 公開は別承認。未決事項が残る場合は synthesis で埋めず、alignment route へ戻す |
| 承認済み spec を垂直 slice と blocking edge にする | `creating-tracer-tickets` | user-invoked | 粒度と依存の承認後に公開する。`blueprint` や `deepening-plan` を置き換えない |
| spec / ticket または direct requirement を実装する | `implementing-work` | user-invoked | unblocked frontier と検証可能な acceptance criterion を前提とする。品質確認と commit / push は global policy に従う |
| 外部から届いた raw issue / PR を agent-ready にする | `triaging-issues` | user-invoked | 生成済み tracer ticket を再 triage しない。comment / label 更新は別承認 |
| 固定点からの差分を Standards / Spec の二軸で見る | `reviewing-code` | model-invoked | read-only review discipline。Phase 4 の mandatory review と出荷判定を置き換えない |
| domain vocabulary を問い直す | `modeling-domains` | model-invoked | glossary / decision vocabulary。process flow の代替にしない |
| module shape、interface、seam を設計する | `designing-codebases` | model-invoked | deep-module vocabulary。実装や broad refactor の許可ではない |
| 新規systemの境界、bounded context、DDD判断を設計する | `software-architecture` | model-invoked | greenfield / major redesignのsystem boundary。既存codebaseの改善surveyや選択済みmoduleの局所改善ではない |
| architecture の deepening opportunity を scoped survey する | `improving-codebase-architecture` | user-invoked | ユーザー指定範囲または recent git hot spot に絞って HTML 候補を提示する。選択後の設計・実装は別 route |
| 選択済みの1〜3 module または一つの関心事を段階的に改善する | `improving-architecture` | model-invoked | Deletion Test、Seam、Locality で改善案を作る。実装、ADR、broad survey は別 gate |
| session / agent 間へ durable context を渡す | `handing-off-context` | user-invoked | handoff artifact を作る。別 session の起動や外部投稿は行わない |

第三者 Skill の発見、評判、provenance、全件 catalog、導入、更新、廃止は `skill-governance` を入口にする。read-only inventory は model-invoked でよいが、promotion、update、retirement、delete、runtime mutation は user-invoked とし、governance gate を通す。

<!-- skill-governance-contract:routing:start -->
第三者Skillは `skill-governance` で候補catalogとactive runtimeを分離する。read-only inventoryだけをmodel-invokedとし、promotion、update、retirement、delete、runtime mutationはuser-invokedかつ人間承認を必須にする。
<!-- skill-governance-contract:routing:end -->

Tracker、triage label、domain doc layout が hard dependency の route で設定が欠ける場合だけ、`setting-up-engineering-skills` を **user-invoked の提案**として返す。提案しただけでは実行しない。

## External Write Gate

Route 選択だけでは、次の操作を許可しない。

- issue / PR / comment / label、Slack 等の対人送信、Calendar、Drive、production deploy、secret store の更新。
- `git commit` / `git push`。明示された project policy またはユーザー承認に従う。
- prototype branch や tracker artifact の作成。decision evidence と production artifact を分ける。

実行前に対象、操作、本文または差分を確定する。`Agent()` や plugin へ委任しても、この gate は緩和されない。

## Fallbacks

- skill または plugin tool が利用できない場合は存在を捏造せず、no skill / local fallback と欠落機能を明示する。
- `Agent()` / `Workflow` が使えない場合は Claude lead が逐次実行し、同じ acceptance と Phase gate を維持する。
- 複数 route が当てはまる場合は user-visible deliverable を所有する route を primary にし、他は source または review に限定する。
- 起動権が不明な route は自動実行せず、user-invoked として確認する。
