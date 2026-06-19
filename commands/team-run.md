---
name: team-run
description: "複数エージェントが自律協調するAgent Teamを編成してタスクを遂行する（TeamCreate/SendMessage）。Workflowの単一fan-outでは足りない、エージェント間の対話的協調・複数ターンに渡る協働が必要なタスクに使う。"
---

# /team-run — Agent Team オーケストレーション（柱A: 自律協調）

**メインセッション（あなた）= team-lead。全 teammate はメインセッションが直接 spawn する。**

## 使い方

```
/team-run "<タスク説明>"
```

## いつ使うか（3機構の使い分け）

| 機構 | 性質 | 使う場面 |
|------|------|---------|
| **Workflow tool** | 親が一括投入する並列fan-out。ワーカーは独立・短命・相互通信なし | レビュー/調査/A-B比較など大半のLoopタスク（既定） |
| **/team-run (Agent Teams)** | teammate同士が `SendMessage` で対話し、共有タスクリストから自律的に仕事を取る | フルスタック機能(FE/BE並行)、探索+実装+レビューの三つ巴 |
| **/orchestrate** | Codexランタイムでの逐次エージェントチェーン | Codex主体で順序が重要なチェーン |

> 迷ったら Workflow を使う。teammate 間の往復対話が本質的に要る時だけ /team-run。

## Agent Teams の動作モデル（CRITICAL）

```
main session (team-lead)  ← 唯一の spawn 権限者
  ├── planner teammate    → SendMessage で compact 計画を lead に送信
  ├── implementer teammate → 内部で Codex subagent を起動（Codex は teammate ではない）
  └── reviewer teammate   → SendMessage で compact 指摘を lead に送信
```

**制約（公式ドキュメント準拠）:**
- **team-lead = main session のみ**。teammate は他の teammate を spawn できない（No nested teams）
- **全 teammate は main session が直接 `Agent({team_name, ...})` で spawn する**
- teammate からの `SendMessage` が **lead の会話に新しいターンとして届く** → 内容が verbose だと lead のコンテキストを汚染する
- teammate が Codex を使う場合、`Agent({subagent_type: "codex:codex-rescue"})` を**内部から呼ぶ**（Codex は team member ではなく、teammate のコンテキスト内で動く regular subagent）

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

## フロー

0. **PJ設定読込**: 実行PJの `.claude/context/team-run.md` があれば**必ず読み**、以降のチーム編成・通知先・実装方針・レビュー観点に反映する。無ければ PJ CLAUDE.md のチーム/レビュー関連記述を参照。どちらも無ければグローバル既定で進める。（雛形: `templates/project-setup/.claude/context/team-run.md`）

### Phase 1: 計画（メインセッション担当）

1. **前提確認**: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` が settings.json に設定されていること

2. **編成**: `TeamCreate({team_name: <タスクのkebab形式>, agent_type: "team-lead"})`
   > **バージョン注意**:
   > - v2.1.170（現行）: `TeamCreate` が必要
   > - v2.1.178 以降: `TeamCreate`/`TeamDelete` は廃止。`Agent({team_name, ...})` だけで自動セットアップ

3. **planner teammate を spawn**:
   ```
   Agent({
     team_name: <team_name>,
     name: "planner",
     subagent_type: "Plan",
     model: "opus",
     prompt: """
       タスクを最大10件に分解し、blockedBy で依存を明示せよ。
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

4. **人間ゲート（CRITICAL）**: planner が SendMessage で plan JSON を送信してきたら:
   1. JSON を整形してチャットに提示（`mcp__visualize__show_widget` で図示可）
   2. `AskUserQuestion` で承認を取得:
      - **承認** → Phase 2 へ進む
      - **修正要求** → `SendMessage` で planner に修正依頼 → 再提示（最大2回）
      - **却下** → 全 teammate に `SendMessage({type:"shutdown_request"})` して終了
   3. **承認なしに Phase 2 を開始してはならない**

### Phase 2: 実装（メインセッションが全 teammate を spawn）

5. **TaskCreate** で承認済みタスクをリスト登録（`blockedBy` で依存を設定）

5.5. **explorer teammate を spawn**（`type:"explore"` タスクがある場合のみ）:
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

6. **implementer teammate を spawn**（承認後のみ）:
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
       完了時: TaskUpdate でステータスを更新し、lead には以下 JSON のみ SendMessage せよ:
       {"status":"done|blocked","changedFiles":["..."],"summary":"<100字以内>"}
     """
   })
   ```

7. **reviewer teammate を spawn**（implementer の SendMessage 受信後）:
   ```
   Agent({
     team_name: <team_name>,
     name: "reviewer",
     subagent_type: "arch-reviewer",   // または security-reviewer / perf-reviewer
     model: "opus",
     prompt: """
       実装された変更をレビューせよ。
       指摘があれば implementer に直接 SendMessage して修正を依頼してよい（peer-to-peer）。
       lead には最終所見を以下 JSON のみ SendMessage せよ:
       {"findings":[{"severity":"CRITICAL|IMPORTANT|MINOR","message":"<100字以内>"}]}
     """
   })
   ```

8. **品質ゲート**: reviewer の SendMessage を受け取り:
   - CRITICAL/IMPORTANT が残れば implementer に `SendMessage` で修正依頼（最大3回）
   - 全指摘解消 → 終了フローへ

9. **終了**: 全タスク完了 → 各 teammate に `SendMessage({type:"shutdown_request"})`

10. **報告**: 以下を整形してチャットに出力:
    ```
    ## Orchestration Report
    - Status: SHIP | NEEDS_WORK | BLOCKED
    - Changed Files: [...]
    - Review Findings: [...]
    - Blockers: [...]
    ```

### Phase 3: PR作成＋継続監視（実装成果をPRにするタスクの場合）

11. **PR作成＋継続監視**: 「PR作成して終わり」にしない。
    - `/pr` で Draft PR を作成（状態図があれば埋め込み）
    - Draft PR の間は `/pr-watch` は CI のみ監視する。レビューコメント対応まで自動化する場合は Ready for review にしてから継続監視を続ける
    - 作成したPR番号で CI/レビューの30分おき継続監視を起動する。`/loop` は Claude Code built-in の slash command なので、チャットで **`/loop 30m /pr-watch <PR>`** を手動実行する
    - 起動後は CI全green＆レビュー対応完了まで自動対応し続け、完了後 `/pr-watch` が「対応不要」を報告（ユーザーが `Esc` で停止）。同一PRへの監視ループは二重起動しない

## 安全・制約

- 外部書き込み（PR/Jira/Slack）は冪等に（既存検索→更新 or 新規）
- teammate 数は4目安、差し戻しは最大3回（無限ループ防止）
- teammate が idle でも慌てない（idle=入力待ち。メッセージで起こせる）
- `teams/` 配下に実行時状態が生成される（v2.1.178+ は自動クリーンアップ）
- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` が settings.json に設定されていること

## 参照

- `<project-root>/.claude/context/team-run.md` — **PJ固有設定**（通知チャンネル・実装方針・編成デフォルト・レビュー観点）。雛形: `templates/project-setup/.claude/context/team-run.md`
- `agents/orchestrator.md` — team-lead（指揮者）の役割定義
- `context/loop-engineering.md` — 実行モデルの正典
- `skills/autonomous-loops/SKILL.md` — DAG/PRループのパターン
- `commands/pr-watch.md` — 完了後のCI/レビュー継続監視（Phase 3で起動）
