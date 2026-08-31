# メモリとartifactの形式

この文書は、task memory、Roadmap、delivery evidence、知識indexの形式を定める正本である。workflowの順序は context/workflow-rules.md、Skill・委譲は context/agent-team-routing.md、HTML表示は skills/viewing-plans/SKILL.md を参照する。

CodexとClaudeのdocsはruntime別の入口として必要な差異を持つ。task-context、sync-roadmap、Evidence Bundle schemaはCodex側の共通実装を正本とし、両scopeのMarkdownをbyte同一に保つ契約は置かない。

## 配置

MEMORY_DIRはプロジェクトのAGENTS.mdで定め、未定義なら .local/ とする。taskは MEMORY_DIR/memory/YYMMDD_<task>/ に保存する。

    .local/
    ├── memory/YYMMDD_<task>/
    │   ├── 00_spec.md  # 要件（必要時）
    │   ├── 05_log.md   # 指示、判断、実行、検証
    │   ├── 20_survey.md
    │   ├── 30_plan.html
    │   ├── 40_progress.md  # HTML計画では任意の作業メモ
    │   ├── 80_review.md
    │   ├── 90_verification.md
    │   ├── handover.md / adr/ / evidence/
    │   ├── roadmap.html / roadmap-snapshot.json
    │   └── task-meta.json
    ├── memories/<category>/  # 検索用の短いindex
    ├── solutions/<category>/ # 再利用可能な解決策
    └── issues/                # review / defect record

routeがlog-onlyなら、05_log.md以外のartifactを必須にしない。roadmap / explicit-roadmapでは30_plan.htmlとRoadmapを保存し、必要なacceptance・review・evidenceをrouteに応じて接続する。

## task metadataとsession復元

task-meta.jsonはgeneratorが管理するmachine-owned manifestである。人がPhaseやCodemap状態を重複管理しない。

    {"schema_version":1,"task_id":"YYMMDD_task","task_title":"表示名",
     "thread_id":"...","session_id":"...","project_path":"/abs/project",
     "worktree_path":"/abs/worktree","task_state":"active","code_change":true,
     "created_at":"2026-08-31T12:00:00+09:00","updated_at":"..."}

必須は schema_version、task_id、task_title、project_path、worktree_path、task_state、code_change、created_at、updated_at。task_stateは active / waiting / verifying / completed / archived。thread_id、session_id、approval_stateは任意である。絶対pathは実在する対象を指す。

復元は session ID、次に thread IDの完全一致を優先する。不一致のtaskを最新時刻、名前、pathだけで自動選択しない。完全一致がなく、active / waiting / verifyingが一件だけなら互換fallbackを使えるが、理由を05_log.mdに記録する。複数候補、metadata破損、context不一致は候補を提示し、停止または明示選択へ戻す。handovers/<session-id>.mdを正本とし、HANDOVER.mdは互換pointerに留める。runtime/locksはworktree固有とする。

## 05_log.md

05_log.mdにはユーザー指示、phase、判断、試行、コマンドの結果、review、未確定、次actionを時系列で追記する。自由文の完了宣言だけでartifactやevidenceを代用しない。

変更・実装taskでは、route、実装単位、acceptance、write scopeを決めた直後、対象成果物の最初のwriteより前に次のDelegation Decisionを保存する。判断がmaterialに変わったら supersedes を付けて再記録する。

    ## YYYY-MM-DD HH:MM - Delegation Decision
    - decision: worker | lead | N/A (read-only)
    - role: worker | implementer | N/A
    - gate: PASS | FAIL | N/A
    - decision_unit: <Work Packetまたは実装単位>
    - passed_conditions: <Local-first、委譲利益、独立証拠、Write scope、外部副作用>
    - failed_conditions: <不成立条件またはnone>
    - local_first_evidence: <pathまたはcommand>
    - reason: <具体的理由>
    - write_scope: <担当pathまたは責務>
    - acceptance: <成果物とfresh検証条件>
    - supersedes: <日時またはnone>
    - lead_retains: integration, source verification, fresh validation, final decision, external write

Phase 2 artifact保存後は、全routeで `~/.codex/scripts/sync-roadmap.py` の検査結果を記録する。Phase 3/4/5も同じTASK、root、run-idでphaseだけを変える。log-onlyではRoadmap生成skipを記録する。

## 00_spec.md と30_plan.html

00_spec.mdは概要、背景・目的、現在の事実、採用判断、未確定、必須/任意要件、非機能要件、制約を持つ。

新規計画の正本はUTF-8の`30_plan.html`であり、`30_plan.md`を新しく作らない。

見えるsemantic HTMLが本文を所有する。Taskは`data-task-id`を持つsectionと見出し、項目は`data-field`で結ぶ。`purpose`、`targets`、`implementation`、`outputs`、`verification`が基本項目で、`acceptance`、`required-sources`、`implementation-evidence`、`blocked-by`を必要に応じて加える。本文をJSONや隠れたMarkdownへ重複保存しない。

本文の最小構成例（headにはcharset・viewport・title・artifact-kind・CSPと必要なinline CSSを置く）:

```html
<main id="plan-document" data-plan-schema="2">
  <h1 data-plan-title>計画の題名</h1>
  <p data-plan-intro>背景と到達点を具体的に書く。</p>
  <section data-field="required-sources">
    <ul>
      <li data-source-ref="task:30_plan.html">計画の正本</li>
      <li data-source-ref="workspace:src/example.py">実装と検証の対象</li>
    </ul>
  </section>
  <section data-task-id="1" data-ui-change="false">
    <h2>実装すること</h2>
    <section data-field="purpose"><h3>目的</h3><p>達成する状態。</p></section>
    <section data-field="targets"><h3>変更対象</h3><p>src/example.py</p></section>
    <section data-field="implementation"><h3>実装</h3>
      <ul><li><input type="checkbox" disabled>必要な手順。</li></ul>
    </section>
    <section data-field="outputs"><h3>成果物</h3><p>確認できる出力。</p></section>
    <section data-field="verification"><h3>検証</h3><p>実際に確かめる方法。</p></section>
    <section data-field="acceptance"><h3>受入条件</h3>
      <ul><li data-acceptance-id="A1">期待する結果。</li></ul>
    </section>
  </section>
</main>
```

チェック状態はnative checkboxの`checked`または`data-complete`へ置く。Task statusとdone/totalを明示する場合は実際のstepsと一致させる。依存は`data-task-ref`、acceptanceは`data-acceptance-id`、根拠は`data-source-ref`に記録し、並びから推測しない。HTML形式では進捗もHTMLが所有し、`40_progress.md`は任意の作業メモであって状態を上書きしない。

UI変更のTaskは`data-ui-change="true"`と同じTask内の`script[type="application/json"][data-plan-fragment="ui-preview"]`を使う。payload・固定baseRef・Before/After・uncertaintyの規則は`skills/viewing-plans/references/ui-change-preview.md`へ集約する。implementation diagramは同じ型の`data-plan-fragment="diagram"`。実行script・event handler・外部resource・本文の隠蔽を許可しない。機械用JSONで`<`を含む値を書く場合はscript終端を作らないようUnicode escapeする。

HTMLの解釈、許可要素・属性・値・サイズ上限の正本は`scripts/roadmap_plan_contract.py`の共通実装である。全consumerはread-onlyの安全resolver/modelを使い、HTMLをMarkdownへ変換して旧parserへ渡さない。正本のraw UTF-8 bytesからhashを計算し、生成SVGやreceiptを同じsourceへ埋めて自己参照させない。`planSourceRawSha256`は両形式のraw bytesを照合する共通fieldであり、legacyの改行正規化済み`sourceHashes`とは区別する。

Phase 5では`required-sources`に最低限`task:30_plan.html`と、実装・検証に使う一つ以上の`task:`または`workspace:<repo-relative-file>`を列挙する。checkpointが存在するときだけその参照とID/hashも加える。Evidence Bundleのsource_fingerprintsは、この宣言と完全一致するcanonical keyのSHA-256を持つ。log-onlyにはこのcompletion契約を強制しない。

### 既存Markdownとの互換

既存taskはHTMLがない場合だけ`30_plan.md`を従来どおり読み、`40_progress.md`の既存挙動・hash・completion条件も維持する。両方存在すればHTMLだけを使い、MD siblingの変更で新しい計画の内容やhashを変えない。不正HTMLをvalidなMDで隠さない。個別移行ではHTMLを追加し、元MDを削除・改名・自動更新しない。全taskの一括移行はしない。 他Skillの過去例に30_plan.mdの参照が残っていても、新規計画は共通resolverが選ぶ30_plan.htmlを使う。

legacy MDのTask heading/required_sources/ui-preview-jsonは過去入力の互換契約であり、新規authoring手順ではない。legacyだけは`task:30_plan.md`と`task:40_progress.md`をmandatory sourceとして扱う。

実装根拠は`repo:<relative-path>#<anchor-or-Lx-Ly>`で明示する。bare/absolute path、traversal、symlink、secret、binaryを解決しない。新しい図の正本はSVGで、MarkdownへMermaidを追加しない。

## Roadmap snapshot v2

30_plan.htmlが正本で、roadmap.htmlとroadmap-snapshot.jsonは共通parser / generatorから作る派生viewである。派生物を手で直さず、正本を編集したら同じ入力で再生成する。snapshotには選択したplanSourceと、表示用のsafe semantic treeであるplanDocumentを持つ。

Plan解釈は scripts/roadmap_plan_contract.py に一本化する。v2がある場合に構造エラーをv1で隠さない。v1 fallbackはplanを持たない古いsnapshotだけに限る。必須Task、section、source hash、依存が不正なら停止する。

    {
      "schemaVersion": 2,
      "sourceHash": "<sha256>",
      "sourceHashes": {"30_plan.html": "<raw-byte sha256>"},
      "tasks": [{
        "number": "1", "title": "...", "purpose": "...",
        "targets": [], "implementation": [], "outputs": [],
        "verification": [], "blockedBy": "",
        "steps": [{"label": "...", "complete": false}],
        "status": "planned",
        "source": {"file": "30_plan.html", "lineStart": 1, "lineEnd": 20}
      }],
      "edges": [], "progress": {"done": 0, "total": 1,
      "globalComplete": false}, "diagnostics": [],
      "sources": {"plan": "30_plan.html", "progress": "30_plan.html"}
    }

Task graph（tasks / edges）、progress、timeline（05_log.md等の明示イベント）は別の関係として表示する。Task順やmtimeから時系列、完了、担当、期限を推測しない。source lineから正本へ戻れることを表示の完了条件にする。roadmap.html、roadmap-snapshot.json、temporary output、symlinkはartifact metadataのhash対象から除外する。

## Delivery lifecycle artifacts

Evidenceは要件から実行結果へIDとsource hashで結ぶ。下流artifactは正本本文を複製せず、artifact_id、source_hash、acceptance_ids、差分要約と参照を持つ。

### Approved PRD

prd-flow / multi-packet-flowの要件契約。必須fieldは artifact_id、source_hash、objective、scope、out_of_scope、acceptance_ids、review_status。review_statusがpassでない場合は実装へ進めない。reviewerはread-onlyである。

### Work Packet

一つのwriterへ渡す実装単位。必須fieldは次の通り。

    artifact_id, source_hash, objective, scope, out_of_scope,
    owned_paths, acceptance_ids, constraints, capability_class,
    safety_decision_id, side_effects_requested, external_write_targets,
    approval_required, approval_evidence, dry_run_required, baseline,
    reality_contract, verification, dependencies, handoff_requirements,
    reviewer_focus, journey_scenarios, negative_paths, completion_target

owned_pathsはscope内に限定し、同一roundでwriterを一人に固定する。該当しない項目は空欄でなく N/A: <理由> と書く。reality_contractはsource model、legacy data、production topology、MUST / MUST NOT、認証・PII・external writeを明示する。completion_targetは implemented / wired / piloted / effective / adopted のいずれかである。approval_requiredがtrueなら、trusted runtimeがapproval_evidenceの実在とhashを検査する。

### Evidence Bundle

makerがdraftを作り、独立checkerがreview sectionを完成させる。必須fieldは次の通り。

    artifact_id, source_hash, source_fingerprints, evidence_fingerprints,
    acceptance_evidence, tests, findings,
    residual_risks, writes_performed, safety_decision_id, policy_source,
    lineage, journey_evidence, negative_path_evidence,
    completion_state, completion_evidence（effective / adoptedを主張する場合）

completion_stateは実測した段階だけにする。implementedはcode / schema / docsと直接test、wiredはruntime entrypoint到達、pilotedは実sample、effectiveはbaseline比の改善、adoptedはowner・人間承認・rollback・review dateを意味する。effective / adoptedを主張する場合だけ、labelではなくsource-bound completion_evidence（status: pass、state / source_hash一致、checks非空）を要求する。Work Packetのcompletion_target未達ならdeliveryせず WIRE / PILOT / MEASURE / ADOPT へ戻す。

`acceptance_evidence`は各IDを`<ID>|PASS|source:task:90_verification.md#L1`の形で一件ずつ結び、同じverification fileで複数IDを証明してよい。`evidence_fingerprints`のkeyはfragmentなしのcanonical source fileとし、同一fileは一keyにまとめてsha256を記録する。`work-packet.json`がある場合、`owned_paths`は`required_sources`に含まれるrepo-relative FILE pathだけにする（required_sourcesにはread-only依存も含め得る）。`writes_performed`はその宣言済みworkspace pathだけにする。workspaceを書かなかった場合だけ`writes_performed`を厳密に`["N/A: no workspace writes"]`とでき、混在や別の自由文は許可しない。packetがないcompletionは`implemented`だけを許可する。

### Delivery Draft Input

Evidence Bundleとtrusted Git snapshotからcommit / PR文案を作る一時入力。必須fieldは draft_id、draft_kind、source_hash、changed_paths、evidence_bundle_id、acceptance_ids、test_ids、residual_risk_ids、template_sections、policy_source。第二のlifecycleや永続diffを作らない。

### Delivery Draft Output

Fast workerまたはleadが返す未信頼の文案。必須fieldは draft_id、draft_kind、source_hash、status（DRAFT_READY / DRAFT_BLOCKED）、claim_references、content。claim_referencesは許可されたchanged path、acceptance、test、riskだけを参照し、親がtrusted snapshotとEvidenceへ戻って検証する。

### Escaped Defect Record

delivery後の漏れを最初に防げたgateへ戻すrecord。必須fieldは record_id、source_trust: external_untrusted、source_comment_id、failure_classes、earliest_preventable_gates、verified_against、allowed_fix_scope、rejected_instruction_reason、promotion_level（L0 / L1 / L2 / L3 / L4）、promotion_targets、approval_required、approval_evidence、owner、review_date、rollback、safety_decision_id。外部comment本文を命令として実行せず、diff / test / logで確認する。policy対象のpromotionはlevelに関係なく人間承認を要する。

### Canonical safety decision

安全判断はtask内で一つにし、Work PacketとEvidence Bundleが同じ safety_decision_id を参照する。trigger、対象、必要な承認、証跡、dry-run、最終stateを持つ。外部write、runtime policy昇格、権限、課金、認証、不可逆操作の承認を自己申告で補わない。

## 40_progress / review / verification

HTML計画では進捗を30_plan.htmlへ記録し、40_progress.mdは時刻や問題・対応を残す必要がある場合だけ使う。既存MD計画では40_progress.mdによる従来の進捗管理を維持する。80_review.md / 90_verification.mdは実行した検査、finding、判定、残課題と参照を持つ。log-onlyで不要なartifactを作らない。

## memories と solutions

memoriesは短い検索index、solutionsは再利用可能な解決策であり、詳細ログの代替にしない。

memoriesの必須frontmatter:

    ---
    summary: "検索で判断できる1–2行"
    created: 2026-08-31
    ---

solutionsの必須frontmatterは title と created。新規memories / solutionsには、知見が有効な phases（preparation、investigation、planning、implementation、quality-check、reporting、compound）と related task pathを付ける。本文は問題、根拠、対策、回帰検査、採否を短く記す。

検索は memories の summary / tags、solutions の title / tags / root_cause / component / problem_typeをrgで行う。SQLiteが有効な環境でもMarkdownが正本である。runtimeが無効なら自動保存・自動注入を実行済みと扱わない。

## JIT brief、token、共有

再開時に実装者へ渡すJIT briefは、objective、次の未完了Task、targets、dependencies、verification、decisions、unknowns、source refsだけを含める。会話全文、secret、認証済みsession、tool output全文を渡さない。task-contextは`~/.codex/scripts/task-context.py`を明示root・指定task付きで使い、引数と出力schemaはcontext helperの実装・testを正本とし、この文書で捏造しない。list / brief helperはread-onlyに限定する。

    python3 ~/.codex/scripts/task-context.py list --memory-root ROOT --limit N
    python3 ~/.codex/scripts/task-context.py brief TASK --memory-root ROOT [--task-id ID]

listの`--memory-root ROOT`は繰り返し指定でき、briefの`--task-id ID`は任意である。

tokenとload量は単位を分けて記録する。

- measured tokens: tokenizerで実測したinput / output token（取得できた場合）。
- measured bytes: file / streamの読込・書込byte。
- measured runtime: 実行時間、試行回数などの観測値。
- proxy: 行数、呼び出し数、概算token、artifact数などの近似値。

proxyをmeasured、構文PASSをuser outcome、自由文をEvidenceと呼ばない。実行開始・retry・完了・失敗とbounded retryは05_log.mdへsecretなしで記録する。

worktree間ではmemories、solutions、issues、memory（namespaced）を共有してよいが、handovers、HANDOVER.md、runtime、plansはworktree固有に保つ。既存hookの登録がない共有を実行済みと扱わない。
