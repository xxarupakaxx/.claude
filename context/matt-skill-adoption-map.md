# Matt Skill adoption map

固定revision：`9603c1cc8118d08bc1b3bf34cf714f62178dea3b`

この文書は、固定revisionに含まれる41 Skillの採否判断とuser-scope routeを保持する。

実装状態の正本はgovernance catalog、registry、runtime routingであり、この文書は判断coverageと理由の確認に使う。

| # | Upstream | Stage | Decision | User-scope route | Reason |
| ---: | --- | --- | --- | --- | --- |
| 1 | `design-an-interface` | deprecated | retire | `brainstorming`、`designing-codebases` | 旧sub-agent API前提の同名local Skillも削除し、意図探索と境界設計へ分離する |
| 2 | `qa` | deprecated | retire | `triaging-issues`、`diagnosing-bugs` | QA sessionの責務をissue化と診断へ分離する |
| 3 | `request-refactor-plan` | deprecated | retire | architecture survey、`to-spec`、`to-tickets` | 計画と外部issue作成を分離する |
| 4 | `ubiquitous-language` | deprecated | retire | `modeling-domains` | 用語だけでなく境界と曖昧性を同じ規律で扱う |
| 5 | `ask-matt` | stable | adapt | `ask-skill-router` | local全体のroutingへ統合済み |
| 6 | `code-review` | stable | adapt | `reviewing-code` | StandardsとSpecの二軸を維持する |
| 7 | `codebase-design` | stable | adapt | `designing-codebases` | read-only設計規律としてscopeを限定する |
| 8 | `diagnosing-bugs` | stable | keep | `diagnosing-bugs` | 同名のfeedback loopを継続する |
| 9 | `domain-modeling` | stable | adapt | `modeling-domains` | localの用語と境界の成果物へ適合する |
| 10 | `grill-with-docs` | stable | adapt | `grilling-with-docs` | project docsとExternal Write Gateへ適合する |
| 11 | `implement` | stable | adapt | `implement` → `implementing-work` | 正式名entryからglobal Phase 3へ接続する |
| 12 | `improve-codebase-architecture` | stable | adapt | `improving-codebase-architecture` | read-only surveyとhotspot制限を保つ |
| 13 | `prototype` | stable | adapt | `prototyping-solutions` | decision evidenceとproductionを分離する |
| 14 | `research` | stable | keep | `research` | 一次情報優先の共通調査layerを使う |
| 15 | `resolving-merge-conflicts` | stable | keep | `resolving-merge-conflicts` | 同名の意図追跡規律を継続する |
| 16 | `setup-matt-pocock-skills` | stable | adapt | `setting-up-engineering-skills` | trackerがhard dependencyの場合だけ使う |
| 17 | `tdd` | stable | keep | `tdd` | red-green-refactorとtest seamを維持する |
| 18 | `to-spec` | stable | adapt | `to-spec` → `writing-specifications` | 正式名で発見し、外部公開を別承認にする |
| 19 | `to-tickets` | stable | adapt | `to-tickets` → `creating-tracer-tickets` | 正式名で発見し、blocking edgeを保つ |
| 20 | `triage` | stable | adapt | `triaging-issues` | local tracker policyへ適合する |
| 21 | `wayfinder` | stable | adapt | `wayfinder` → `mapping-large-projects` | 正式名で発見し、planning-only境界を保つ |
| 22 | `batch-grill-me` | in-progress | adopt | `batch-grill-me` | 明示起動、round負荷表示、中断可能を条件に採用する |
| 23 | `claude-handoff` | in-progress | adapt | `handing-off-to-claude` | Claude専用、明示起動、shared route外で保持する |
| 24 | `loop-me` | in-progress | replace | `autonomous-loops`、`loop-engineering` | stop ruleとGoalを持つlocal loopを優先する |
| 25 | `setup-ts-deep-modules` | in-progress | adapt | `setting-up-ts-deep-modules` | 対象repoが確定した場合だけ使う |
| 26 | `to-questionnaire` | in-progress | adopt | `to-questionnaire` | 明示起動、local Markdown、外部送信なしを条件に採用する |
| 27 | `wizard` | in-progress | adapt | `generating-setup-wizards` | packageと副作用が確定した場合だけ使う |
| 28 | `writing-beats` | in-progress | keep | `writing-beats` | user-invoked writing laneとして保持する |
| 29 | `writing-fragments` | in-progress | keep | `writing-fragments` | user-invoked writing laneとして保持する |
| 30 | `writing-shape` | in-progress | keep | `writing-shape` | user-invoked writing laneとして保持する |
| 31 | `git-guardrails-claude-code` | misc | adapt | `guarding-git-commands-in-claude-code` | Claude Code対象の明示起動に限定する |
| 32 | `migrate-to-shoehorn` | misc | adapt | `migrating-to-shoehorn` | 対象repoでだけ使う |
| 33 | `scaffold-exercises` | misc | adapt | `scaffolding-exercises` | 教材作成の明示依頼に限定する |
| 34 | `setup-pre-commit` | misc | adapt | `setting-up-pre-commit-hooks` | hook変更を別承認にする |
| 35 | `edit-article` | personal | adapt | `editing-articles` | localの日本語執筆規範へ接続する |
| 36 | `obsidian-vault` | personal | adapt | `managing-obsidian-vaults` | VaultのAGENTSと安全境界を優先する |
| 37 | `grill-me` | productivity | keep | `grill-me` | 一問ずつの安定版入口として保持する |
| 38 | `grilling` | productivity | keep | `grilling` | reusable interview primitiveとして保持する |
| 39 | `handoff` | productivity | adapt | `handing-off-context` | durable artifactを作り、session起動は分離する |
| 40 | `teach` | productivity | adapt | `teach` → `teaching-concepts` | 正式名で発見し、stateful workspaceへ接続する |
| 41 | `writing-great-skills` | productivity | keep | `writing-great-skills` | triggerとcontext負荷の規律として保持する |

## Decision count

| Decision | Count |
| --- | ---: |
| keep | 10 |
| adapt | 24 |
| replace | 1 |
| adopt | 2 |
| retire | 4 |
| total | 41 |
