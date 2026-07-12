# Agent Team Routing

Claude が plugin、skill、`Agent()`、`Workflow` を選ぶための routing SSoT。

- Phase 順序と品質 gate は `context/workflow-rules.md` を優先する。
- model 選択は `rules/model-routing.md` を優先する。
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

## Engineering Lanes

ここに載せるのは shared route として採用した promoted skill と既存の canonical flow だけである。

| Signal | Primary route | 起動権 | 境界 |
|---|---|---|---|
| 要件が曖昧で codebase または状態付き docs がある | `grilling-with-docs` | user-invoked | 同じ文脈で alignment、spec、ticket まで進める。codebase がない場合は `grill-me` |
| 目的地はあるが route がまだ分からない巨大案件 | `mapping-large-projects` | user-invoked | decision map を作る。tracker 書き込みは外部書き込み gate を通す |
| route が分かっており複数 session / PR に分ける | `blueprint` | user-invoked | WU と依存を設計する。未知 route の探索には使わない |
| 会話だけでは決められない一つの design question | `prototyping-solutions` | model-invoked | decision evidence を作る。production 実装ではなく、branch / issue / commit は別 gate |
| 合意済み会話を spec にする | `writing-specifications` | user-invoked | Phase 2 artifact。tracker 公開は別承認 |
| 承認済み spec を垂直 slice と blocking edge にする | `creating-tracer-tickets` | user-invoked | Phase 2-2.5 artifact。`blueprint` や `deepening-plan` を置き換えない |
| spec / ticket を実装する | `implementing-work` | user-invoked | Phase 3 adapter。品質確認と commit / push は global policy に従う |
| 外部から届いた raw issue / PR を agent-ready にする | `triaging-issues` | user-invoked | 生成済み tracer ticket を再 triage しない。comment / label 更新は別承認 |
| 固定点からの差分を Standards / Spec の二軸で見る | `reviewing-code` | model-invoked | read-only review discipline。Phase 4 の mandatory review と出荷判定を置き換えない |
| domain vocabulary を問い直す | `modeling-domains` | model-invoked | glossary / decision vocabulary。process flow の代替にしない |
| module shape、interface、seam を設計する | `designing-codebases` | model-invoked | deep-module vocabulary。実装や broad refactor の許可ではない |
| architecture の deepening opportunity を survey する | `improving-codebase-architecture` | user-invoked | 候補提示と選択まで。選択後の実装は別 route |
| session / agent 間へ durable context を渡す | `handing-off-context` | user-invoked | handoff artifact を作る。別 session の起動や外部投稿は行わない |

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
