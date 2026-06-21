---
name: team-run
description: "team-run を起動すると leader が適材適所で model/専門家/codex に割り当て、合格基準を満たすまで loop engineering で回す Agent Team を編成する。共有メモリ(Team Journal)が周をまたいで失敗を持ち越し『円→螺旋』にする。並列の幅が要る高価値タスク限定。"
---

# /team-run — Agent Team を loop engineering で回す

**メインセッション（あなた）= team-lead。全 teammate はメインセッションが直接 spawn する。**
team-run を起動すると leader（lead エージェント = Claude Code 本体）が司令塔になり、タスクを分解 → 適材適所で割り当て → **合格基準を満たすまで loop で回す**。共有メモリ（Team Journal）が周をまたいで失敗を持ち越し、ループを「同じ円のぐるぐる」でなく「前回の上に積む螺旋」にする。

## 使う前に — 本当にチームが要るか

マルチは単一の約15倍トークン。トークンを揃えると単一が拮抗〜凌駕する報告もある（Stanford）。**まず単一＋良い文脈を基準にし、並列の幅が本当に要る時だけ team-run。**

| 状況 | 使うもの |
|------|---------|
| 逐次依存・同一ファイル・密結合・低価値 | 単一エージェント |
| 独立した短いタスクの並列（レビュー/調査/A-B） | Workflow tool |
| 複数ターン対話で互いの軌跡を見て協調する高価値タスク | team-run |

## loop engineering の形（この設計の核）

```
合格基準を先に定義 → [割り当て→並行実行→検証] を合格まで回す → Budget/Stop で止める
```

価値は「回すこと」でなく **合格基準（検証器）の固さと、止め方** にある。

## 前提（CRITICAL）

- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`（settings.json 設定済み）
- 1セッション1チーム・lead 固定・teammate は lead の会話履歴を引き継がない
- in-process teammate は `/resume` で復元されない → 状態は Team Journal に逃がす（後述）
- teammate 数は4目安、差し戻しは最大3回（無限ループ防止）

| 機構 | 性質 | 使う場面 |
|------|------|---------|
| **Workflow tool** | 親が一括投入する並列fan-out。ワーカーは独立・短命・相互通信なし | レビュー/調査/A-B比較など大半のLoopタスク（既定） |
| **/team-run (Agent Teams)** | teammate同士が `SendMessage` で対話し、共有タスクリストから自律的に仕事を取る | フルスタック機能(FE/BE並行)、探索+実装+レビューの三つ巴 |
| **/orchestrate** | Codexランタイムでの逐次エージェントチェーン | Codex主体で順序が重要なチェーン |

> 迷ったら Workflow を使う。teammate 間の往復対話が本質的に要る時だけ /team-run。

## Agent Teams の動作モデル（CRITICAL）

```
main session (team-lead)  ← 唯一の spawn 権限者
  ├── planner teammate      → SendMessage で compact 計画を lead に送信
  ├── plan-reviewer teammate→ 計画を検証（YAGNI・リスク・依存矛盾）→ approve/needs-revision
  ├── explorer teammate     → コードベース調査（explore タスクがある場合のみ）
  ├── implementer teammate  → 内部で Codex subagent を起動（Codex は teammate ではない）
  ├── reviewer-arch teammate    → arch-reviewer でレビュー（並列）
  ├── reviewer-security teammate→ security-reviewer でレビュー（並列）
  ├── reviewer-quality teammate → code-quality-reviewer でレビュー（並列）
  ├── adversarial-review    → Skill("adversarial-review") で Red/Blue/Auditor パターン
  └── sequential-review     → Skill("sequential-review-pre-pr") でPR前最終チェック
```

**制約（公式ドキュメント準拠）:**
- **team-lead = main session のみ**。teammate は他の teammate を spawn できない（No nested teams）
- **全 teammate は main session が直接 `Agent({team_name, ...})` で spawn する**
- teammate からの `SendMessage` が **lead の会話に新しいターンとして届く** → 内容が verbose だと lead のコンテキストを汚染する
- teammate が Codex を使う場合、`Agent({subagent_type: "codex:codex-rescue"})` を**内部から呼ぶ**（Codex は team member ではなく、teammate のコンテキスト内で動く regular subagent）
- teammate が idle でも慌てない（idle=入力待ち。メッセージで起こせる）
- `teams/` 配下に実行時状態が生成される（v2.1.178+ は自動クリーンアップ）

## コンテキスト保護（CRITICAL）

Agent Teams では teammate の `SendMessage` が lead の会話に届く。
verbose な出力（生コード・差分・ログ）を送られると lead のコンテキストを汚染する。

**全 teammate への指示に必ず含めること:**

```
- lead への SendMessage は「1-3行の compact サマリー」のみ
- 詳細な状態は TaskUpdate の notes に書く
- コードブロック・差分・スタックトレースは SendMessage に含めない
- JSON を送る場合も必ず ≤200字に収める
```

## lead の進捗共有ポリシー

team-lead はユーザー確認待ちで作業を止めすぎず、自律的に進める。
ただし、ユーザーが状況を追えるよう、進捗共有は怠らない。

- 作業開始時に、目的・進め方・編成方針を簡潔に報告する
- Phase遷移時、重要タスク完了時、長時間作業が続く前後に進捗を報告する
- 報告には「完了したこと / 現在やっていること / 次にやること / ブロッカー / ユーザー判断が必要なこと」を含める
- 仕様変更・大きな方針転換・破壊的操作・外部に見える副作用・自動解決できないブロッカーは必ずユーザー確認を取る
- 判断不要な通常作業は確認待ちにせず、TaskCreate/TaskUpdateで状態を更新しながら自律的に進める

## フロー

0. **PJ設定読込**: 実行PJの `.claude/context/team-run.md` があれば**必ず読み**、以降のチーム編成・通知先・実装方針・レビュー観点に反映する。無ければ PJ CLAUDE.md のチーム/レビュー関連記述を参照。どちらも無ければグローバル既定で進める。（雛形: `templates/project-setup/.claude/context/team-run.md`）

### Phase 1: 計画（メインセッション担当・起動時）

1. **前提確認**: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` が settings.json に設定されていること

2. **S1. タスク分解 + 合格基準を先に定義.** 合格基準は **機械判定を背骨**にする（test/型/lint/実行が通る = 嘘をつけない形）。機械判定にできない部分だけ判断ベースにし最小化。

3. **S2. Team Journal 初期化**（`.local/memory/<task>/team-journal.md`）。冒頭の「定位置」に **合格基準 / Budget / leader 状態** を書く。

4. **編成**: `TeamCreate({team_name: <タスクのkebab形式>, agent_type: "team-lead"})`
   > **バージョン注意**:
   > - v2.1.170（現行）: `TeamCreate` が必要
   > - v2.1.178 以降: `TeamCreate`/`TeamDelete` は廃止。`Agent({team_name, ...})` だけで自動セットアップ

5. **planner teammate を spawn**:
   ```
   Agent({
     team_name: <team_name>,
     name: "planner",
     subagent_type: "Plan",
     model: "opus",
     prompt: """
       タスクを最大10件に分解し、blockedBy で依存を明示せよ。
       計画作成が長引く場合は、lead に compact サマリーで途中状況を伝える。
       完了後、以下の JSON を lead に SendMessage せよ（JSON 以外は含めるな）:
       {
         "summary": "<200字以内>",
         "tasks": [{"id":"t1","title":"...","type":"explore|implement|review|test",
                    "description":"<300字以内>","blockedBy":[],"codexRequired":false}],
         "risks": ["..."]
       }
       codexRequired=true: 3ファイル以上 or 複雑な実装
     """
   })
   ```

6. **plan-reviewer teammate を spawn**（planner 受信後・人間ゲート前）:
   ```
   Agent({
     team_name: <team_name>,
     name: "plan-reviewer",
     subagent_type: "arch-reviewer",
     model: "opus",
     prompt: """
       以下の実装計画をレビューせよ（YAGNI違反・過剰分解・リスク漏れ・依存関係の矛盾・実現可能性）。
       lead には以下 JSON のみ SendMessage せよ:
       {"planReview":{"verdict":"approve|needs-revision","issues":["<各≤100字>"],"suggestion":"<修正方針≤200字>"}}
     """
   })
   ```
   - `needs-revision` → `SendMessage` で planner にフィードバック → 計画再送待ち（最大2回）
   - `approve` → 人間ゲートへ

7. **人間ゲート（CRITICAL）**: planner が SendMessage で plan JSON を送信してきたら:
   1. JSON と plan-reviewer の verdict を整形してチャットに提示（`mcp__visualize__show_widget` で図示可）
   2. `AskUserQuestion` で承認を取得:
      - **承認** → Phase 2 へ進む
      - **修正要求** → `SendMessage` で planner に修正依頼 → 再提示（最大2回）
      - **却下** → 全 teammate に `SendMessage({type:"shutdown_request"})` して終了
   3. **承認なしに Phase 2 を開始してはならない**

### Phase 2: 実装（各周＝合格まで繰り返す・メインセッションが全 teammate を spawn）

8. **TaskCreate** で承認済みタスクをリスト登録（`blockedBy` で依存を設定）

9. **S3. 割り当て.** leader が Dispatch Table（`rules/model-routing.md`）で配分（計画=planner/opus・実装=codex・レビュー=専門 reviewer・調査=Explore/sonnet）。spawn prompt に objective/境界/成果物形式 ＋ **前周の失敗の要約を leader が直接 push**。要約は症状（「test が落ちた」）でなく **原因（「なぜその判断が要件と不一致か」）を含める**——症状だけだと次周が同じ原因で別の症状を踏む。

10. **explorer teammate を spawn**（`type:"explore"` タスクがある場合のみ）:
   ```
   Agent({
     team_name: <team_name>,
     name: "explorer",
     subagent_type: "Explore",   // built-in。whole file ではなく excerpt を読む探索特化
     model: "haiku",
     prompt: """
       TaskList の explore タスクを担当し、コードベースを調査せよ。
       **検索ファースト厳守**（`rules/tool-invocation.md`）:
       rg/Grep/Glob で広く絞り込んでから、確定した必要箇所だけ Read する。
       ディレクトリを1ファイルずつ全読みするな。
       完了時: TaskUpdate に発見の詳細を書き、lead には以下 JSON のみ SendMessage せよ:
       {"status":"done","findings":["<各≤80字>"],"keyFiles":["path:line"]}
     """
   })
   ```
   > explore 結果（keyFiles 等）を implementer の spawn プロンプトに渡すと手戻りが減る。
   > 探索を `Explore` 以外（implementer 兼任等）で済ませると1ファイルずつ Read する非効率に陥るので避ける。

11. **implementer teammate を spawn**（承認後のみ）:
   ```
   Agent({
     team_name: <team_name>,
     name: "implementer",
     subagent_type: "implementer",
     model: "sonnet",
     prompt: """
       TaskList で承認済みタスクを取得し実装せよ。
       codexRequired=true のタスクは必ず Agent({subagent_type:"codex:codex-rescue"}) で Codex に委任。
       Codex は teammate ではなく、あなたのコンテキスト内で動く subagent として扱う。
       各タスクの開始・完了・blocked は TaskUpdate で必ず更新し、lead がユーザーへ進捗共有できる状態を保つ。
       完了時: TaskUpdate でステータスを更新し、lead には以下 JSON のみ SendMessage せよ:
       {"status":"done|blocked","changedFiles":["..."],"summary":"<100字以内>"}
     """
   })
   ```

12. **S4. 並行実行 / S5. 共有.** 依存のないものだけ同時並行。依存があるもの（実装→レビュー）は順次。各 teammate は自分のセクションに append（`cat >>`）で軌跡を Journal に残す。

13a. **専門 reviewer teammates を並列 spawn**（implementer の SendMessage 受信後）:
   ```
   // 並列で3つ spawn
   Agent({ name: "reviewer-arch",     subagent_type: "arch-reviewer",         model: "opus", ... })
   Agent({ name: "reviewer-security", subagent_type: "security-reviewer",     model: "opus", ... })
   Agent({ name: "reviewer-quality",  subagent_type: "code-quality-reviewer", model: "opus", ... })
   ```
   各 reviewer への指示:
   ```
   実装された変更をレビューせよ。
   lead には最終所見を以下 JSON のみ SendMessage せよ:
   {"findings":[{"severity":"CRITICAL|IMPORTANT|MINOR","message":"<100字以内>"}]}
   ```
   - 全員の findings 収集後、CRITICAL/IMPORTANT があれば implementer に修正依頼（最大3回）
   - 全指摘解消 → Step 13b へ

13. **S6. maker/checker（ペルソナで分業）.** codex（maker）の「できた」は checker が通すまで**未完了**:
   - **maker**=codex（test を改変しない誠実な実装を spawn で課す）/ **checker**=既存の専門 reviewer（MCP・スキル非依存のものを選ぶ）/ **Auditor**=`adversarial-review` の審判（**決裂＝同一 finding で2往復しても不合格、の時だけ**発動）
   - (a) **デフォルト不合格**（CRITICAL/IMPORTANT についてのみ）。合格は根拠を Journal に書く（立証責任の反転）
   - (b) checker に maker の自己申告を見せず、成果物だけ渡す
   - (c) arch/security/perf が各観点で見て 1つでも CRITICAL なら不合格
   - (d) checker は **test の差分も疑う**（test を緩めた/skip/削除した形跡＝不合格・reward hacking 対策）
   - **合格ライン**: 機械判定 green ＋ 全 checker の CRITICAL/IMPORTANT がゼロ。**MINOR は合格を妨げない**（完璧主義を抑制し loop を収束させる）
   - 合否が割れたら不合格優先 → 決裂が続けば Auditor が裁定 → なお決まらねば human に escalate

13b. **adversarial-review を実行**（専門 reviewers が全 MINOR 以下になった後）:
   ```
   Skill("adversarial-review")
   ```
   - ESCALATE / 採用された CRITICAL があれば implementer に修正依頼 → 解消後 Step 13c へ
   - 指摘なし → Step 13c へ

13c. **PR前レビュー（sequential-review-pre-pr）を実行**:
   ```
   Skill("sequential-review-pre-pr")
   ```
   - CRITICAL/IMPORTANT が残れば implementer に修正依頼。全指摘解消後 → 検証へ

14. **S7. 検証（2段）.** ①各タスクが個別に合格基準を満たすか → ②**統合後に全体を再検証**（結合状態で test/型/ビルドが通るか）。並行成果は個別 green でも結合で型不整合・API 食い違いが出る（Flappy Bird の結合版）。**①②両方 green で初めて合格**。満たさなければ失敗を Attribution に記録 → 修正して次周（S3 へ）。

15. **S8. Budget/Stop.** lead の自制心に頼らず **hook（`team-budget-guard.sh`・SubagentStop）で強制**。差し戻しの定義は **Team Journal の Attribution 節に記録された1行**で、hook がその行数を数えて閾値（≤3）超過を検知し、`exit 2` で leader に停止を促して human に escalate する。SSoT は `skills/autonomous-loops/SKILL.md`（差し戻し≤3・連続2失敗で escalate・teammate≤4）。

16. **品質ゲート**: 13a → 13b → 13c → S7 の全ステップで CRITICAL/IMPORTANT がゼロになり、①②両方 green になったことを確認してから終了へ進む。

### 終了時

17. **S9. 統合 + 報告.** leader が統合 → Orchestration Report（`agents/orchestrator.md` 形式）。各 teammate に `SendMessage({type:"shutdown_request"})` してから以下を整形してチャットに出力:
    ```
    ## Orchestration Report
    - Status: SHIP | NEEDS_WORK | BLOCKED
    - Task Status: done / in_progress / blocked / pending の件数と主要タスク
    - Changed Files: [...]
    - Review Findings: [...]
    - Blockers: [...]
    ```

18. **S10. 複利化.** 価値ある知見・失敗を `compounding-knowledge` で `solutions/` へ（次 loop に活かす）。

> **eval 接続点（将来）**: team-run の良し悪しを測る生データは Team Journal にある——タスク完了率 / 差し戻し回数 / 決定の手戻りを Trace・Attribution 節から集計でき pass@k の入力になる（`skills/eval-harness/SKILL.md`）。本格 eval は別タスク。

19. **外部書き込み**（PR/Jira/Slack）は冪等に（既存検索→更新 or 新規）。

### Phase 3: PR作成＋継続監視（実装成果をPRにするタスクの場合）

20. **PR作成（自律）**: `Skill("/pr")` を invoke して Draft PR を作成。PR番号を取得する。
    - 状態図（`91_state_diagram.md`）があれば自動的に埋め込まれる
    - Draft PR の間は CI のみ監視し、レビューコメント対応は Ready for review 後

21. **pr-watch 初回サイクル（自律）**: `Skill("/pr-watch")` を invoke して即時1サイクル実行。
    - CI 実行中（pending）なら結果を記録して次の案内へ
    - CI 失敗があれば自動修正→push まで実行

22. **継続監視の案内**: ユーザーへ報告:
    ```
    PR作成完了: <PR URL>
    継続監視を開始するには: /pr-watch <PR番号>（自動でループ起動・Esc で停止）
    ```
    - `ScheduleWakeup` が利用可能な環境では次サイクルをスケジュールしてもよい
    - 同一PRへの監視ループは二重起動しない（/pr-watch 側で state により制御）

## Team Journal テンプレート（S2 で生成）

冒頭の「定位置」は leader と teammate が毎回読む場所。leader の状態もここに置き、**leader のコンテキストはキャッシュ・真実は Journal**（leader が腐っても定位置から復元）。定位置は **leader 単独が更新**し、teammate は自分の Trace セクションに append のみ（lost-update 回避）。

```markdown
# Team Journal: <task-name>
> 使い方: ①turn 開始前に定位置と直近 Attribution を読む ②turn 終了時に自分のセクションへ append（他人のは触らない）

## 定位置（leader 単独が毎周更新）
- 合格基準: （機械判定: … / 判断ベース: …）
- Budget 残: teammate _/4 ・差し戻し _/3 ・連続失敗 _
- 現在の周: N / 直近の失敗（原因）: …

## 決定ログ Decision Log
| 時刻 | agent | 決定 | 理由 |

## 軌跡 Trace（各 teammate のセクション）
### [agent-name]
- やったこと / 成果物 file:line / 申し送り / ブロッカー

## 失敗・差し戻し Attribution
| agent | task | 失敗内容 | 原因 | ラウンド |
```

## 参照

- `<project-root>/.claude/context/team-run.md` — **PJ固有設定**（通知チャンネル・実装方針・編成デフォルト・レビュー観点）。雛形: `templates/project-setup/.claude/context/team-run.md`
- `agents/orchestrator.md` — team-lead（指揮者）の役割定義
- `rules/model-routing.md` — 適材適所の割り当て（SSoT）
- `skills/autonomous-loops/SKILL.md` — DAG/PRループのパターン・Budget/Stop の SSoT
- `skills/compounding-knowledge/SKILL.md` — 完了後の複利化
- `context/loop-engineering.md` — 実行モデルの正典
- `commands/pr-watch.md` — 完了後のCI/レビュー継続監視（Phase 3で起動）
- 公式: https://code.claude.com/docs/en/agent-teams.md

> **依存**: S8 の Budget/Stop 強制は `team-budget-guard.sh`（SubagentStop に登録）。
> **設計判断（grill で決着・design.md 参照）**: maker/checker タイブレーク=Auditor 裁定 / チーム縮退=対処不要(idle は無料) / DAG=疑わしきは順次+owner 分離+S7 統合検証で後追い。
