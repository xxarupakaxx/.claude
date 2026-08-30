# 作業ルール（Phase 0–5.5）

この文書はClaude user-scopeの作業順序と遷移gateの正本である。artifact形式は context/memory-file-formats.md、委譲とSkillは context/agent-team-routing.md、条件付きgateは context/workflow-details.md、Task Workspaceは skills/viewing-plans/SKILL.md と context/codemap.mdを参照する。

## 既定lane

通常の作業は、把握（Phase 0–1）→計画（Phase 2–2.5）→実装と検証（Phase 3–4.5）→完了と学習（Phase 5–5.5）で進める。既存Phase番号、成果物名、互換表示を維持する。

Phase 0でrouteを一つ選び05_log.mdへ記録する。

| route | 適用 | 必須の表示・保存 |
|---|---|---|
| log-only | 既知手順を一回の実行・検証で閉じる | 05_log.md。30_plan、HTML、Evidence Bundleは要求しない |
| roadmap | 設計判断、複数Task、依存、継続共有、引継ぎがある | 30_plan.md → 共通sync → roadmap.html |
| explicit-roadmap | ユーザーが計画またはRoadmap表示を明示 | roadmapと同じ。表示を省略しない |

ファイル数だけでrouteを決めない。条件付きgate（Fast Track、Blueprint、Goal、UI/UX、HTML）は context/workflow-details.md を発火時だけ読む。log-onlyでもPhase記録、安全条件、fresh検証は省略しない。

### Phase 0: 準備

1. 最も近いAGENTS.md / CLAUDE.mdとproject正本を読み、MEMORY_DIR（未定義なら .local/）とwrite境界を確定する。
2. MEMORY_DIR/memory/YYMMDD_<task>/を作り、05_log.mdに指示、Goal、acceptance、仮定、不明点、trade-off、roadmap_routeを記録する。
3. session ID、次にthread IDの完全一致でhandover/taskを復元する。最新時刻、名前、pathだけで自動選択しない。一件だけの互換fallbackは理由を記録する。
4. memories、solutions、issuesをlocal-firstで検索し、必要なJIT briefを作る。コード変更は編集前後にCodemap gateを通す。

### Phase 1: 把握と調査

既存実装、test、設定、実行経路、関連artifactを先に確認する。変化するAPI、未知の仕様、明示依頼には一次資料を読み、出典と不確実性を記録する。低risk log-onlyに不要な外部調査を強制しない。GO / CONDITIONAL / NO-GO / DEFERと依存・リスク・再開条件を05_log.mdへ記録する。

persistent Goal、/team-run、Goal toolを使う場合は、baselineと観測可能なoutcomeを確認し、条件付きGoal readiness gateを通す。

### Phase 2: 計画

roadmap routeでは30_plan.mdをLLMと人の正本として保存する。Taskごとに目的、変更対象、実装、成果物、検証、acceptance ID、blockedBy、source、write scopeを対応させる。roadmap.htmlとsnapshotは既存parser / generatorの派生viewであり、LLMや手編集で作らない。

Phase 2 artifactとDelegation Decisionを保存した後、Claudeからは次の共有CLIを実行する。

    python3 ~/.codex/scripts/sync-roadmap.py TASK --workspace-root ~/.claude --memory-root ~/.claude/.local/memory --run-id RUN --phase 2

phase 3、4、5も同じtask、workspace-root、memory-root、run-idでphaseだけを変える。--dry-runはread-onlyである。CLIがない、引数が不正、syncが失敗した場合は停止し、旧generatorや別CLIへfallbackしない。log-onlyは検査後のskip結果を05_log.mdへ記録する。

DeepeningとADRは不確実性またはcriteriaが発火した場合だけ行う。コード変更ではrules/complexity-budget.mdのtargetを記録し、実装時actual、review時varianceを更新する。targetを守るために安全性、test、必要機能を削らない。

### Phase 2.5: Acceptance Contract

roadmap routeではGoal / requirement → TaskまたはWU → acceptance → evidenceを一意にたどれるようにする。negative pathとholistic checkを含め、未対応IDや自由文の完了宣言で代用しない。log-onlyにcheckpoint、HTML、Evidence Bundleを強制しない。

### Phase 3: 実装

開始前に最新のDelegation Decision、route、acceptance、write scopeを確認する。Agent()やWorkflowはcontext/agent-team-routing.mdのGateを満たす独立単位にだけ使い、密結合の作業はleadが行う。同じfileのwriterを複数にしない。

実装者には目的、次の未完了Task、対象、依存、検証、決定、不明点、source参照だけからなるJIT briefを渡す。会話全文、secret、認証済みsession、全tool outputは渡さない。task-contextは`~/.codex/scripts/task-context.py`を明示root・task付きで使い、引数と出力schemaはcontext helperの実装とtestを正本にし、ここで発明しない。

### Phase 4: 品質確認

freshな直接検証を先に行う。projectのlint / format / typecheck / test、Markdown・リンク・frontmatter、必要なHTML/Codemap gateを実行する。roadmap routeのcompletion検査は共通syncとEvidence validatorへ接続し、log-onlyではEvidence Bundleを要求しない。

リスクに合う最小の独立checkerを選び、結果、finding、再検証、skip理由を05_log.mdへ記録する。CRITICALと正しさに関わるIMPORTANT / MINORは修正する。未解決finding、stale source、未対応acceptanceがあればPhase 2または3へ戻す。

### Phase 4.5: 引継ぎ

再開に必要なhandover、変更量のtarget / actual / variance、検証、残課題を保存する。Markdown変更後は全文を再読し、矛盾と重複を同じturnで直す。

## Delivery lifecycleと自律LOOP

これは既存のartifact/state互換契約を参照する節で、新しいlifecycleを追加しない。Claudeのstate更新とRoadmap同期は共有CLIを使い、未配線の機能を実行済みと主張しない。

| state | 必要条件 | 次action | 停止・戻り先 |
|---|---|---|---|
| RECEIVED | taskと05_log.md | SURVEY | 調査不能なら WAITING_HUMAN |
| SURVEYED | route decision | PRDまたはWork Packet | model不在なら ROUTING_BLOCKED |
| IMPLEMENTED | Work Packet | REVIEW | 失敗はbounded retry |
| REVIEWED | CRITICAL / IMPORTANTが0 | Evidenceとcompletion target照合 | findingはFIX、不足は WIRE / PILOT / MEASURE / ADOPT |
| DELIVERED | delivery evidence | 完了またはdefect record | 漏れはRECORD_ESCAPED_DEFECT |
| REPLAYED | replay PASS | COMPLETE | 防止不能ならWAITING_HUMAN |

completionは単一booleanでなく implemented < wired < piloted < effective < adopted の順で扱う。unit testだけでwired、sample 0件でpiloted、baselineなしでeffective、owner・承認・rollbackなしでadoptedとしない。completion_target未達は完了にせず、WIRE / PILOT / MEASURE / ADOPTへ戻す。retry上限、承認なしの外部write、権限・課金・認証・不可逆操作・runtime policy昇格はWAITING_HUMAN、必要model不在は弱いmodelへfallbackせずROUTING_BLOCKEDで停止する。

### Workflow route

Workflow routeは工程の形で、Local / Fast / Standard / Heavy / Judgmentのcapability classとは別軸である。fast-track、prd-flow、multi-packet-flowの条件とWork Packetはmemory形式とroutingを正本とする。

### Phase 5: 完了

変更、検証、review、残課題、route、completion_state、completion_target、commit / pushの状態を報告する。構文・機械PASSとuser outcomeを分ける。measured tokens（tokenizerで実測した入出力token）、measured bytes（読込・書込byte）、proxy（行数、呼び出し数、概算token）を別記録し、proxyを実測tokenと呼ばない。外部writeは承認証跡がある場合だけ行う。

### Phase 5.5: Compound / 改善

再利用価値のある失敗・成功を候補として記録し、trialで回帰検査と外部feedbackを確認してからadoptする。adoptにはowner、承認、rollback、review dateを付ける。外部feedbackなしの自動policy promotion、Skill / hook / contextの自動更新は行わない。memories / solutionsにはphasesとrelatedを付ける。

## 安全と完了境界

外部更新、public share、git push、権限・課金・認証変更、削除・不可逆上書き、secret操作は対象・差分・principal・承認・dry-runを確定してからleadが行う。権限errorやcontext不一致を別principalへ自動切替しない。主経路の失敗を旧generatorや別CLIで隠さない。

関連:
- context/workflow-details.md
- context/memory-file-formats.md
- context/agent-team-routing.md
- skills/viewing-plans/SKILL.md
- context/codemap.md
- context/html-artifact-contract.md と config/html-surfaces.json
- rules/model-routing.md、rules/complexity-budget.md、rules/security.md
