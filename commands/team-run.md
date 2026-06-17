---
name: team-run
description: "複数エージェントが自律協調するAgent Teamを編成してタスクを遂行する（TeamCreate/SendMessage）。Workflowの単一fan-outでは足りない、エージェント間の対話的協調・複数ターンに渡る協働が必要なタスクに使う。"
---

# /team-run — Agent Team オーケストレーション（柱A: 自律協調）

**メインセッション（あなた）は thin conductor として振る舞う。**
実作業はすべてサブエージェントに委任し、自身のコンテキストウィンドウを保護する。

## 使い方

```
/team-run "<タスク説明>"
```

## いつ使うか（3機構の使い分け）

| 機構 | 性質 | 使う場面 |
|------|------|---------|
| **Workflow tool** | 親が一括投入する並列fan-out。ワーカーは独立・短命・相互通信なし | レビュー/調査/A-B比較など大半のLoopタスク（既定） |
| **/team-run (Agent Teams)** | エージェント同士が `SendMessage` で対話し、共有タスクリストから自律的に仕事を取り、**複数ターンに渡って協調** | フルスタック機能(FE/BE並行)、探索+実装+レビューの三つ巴、長時間の協働 |
| **/orchestrate** | Codexランタイムでの逐次エージェントチェーン（ハンドオフ文書） | Codex主体で順序が重要なチェーン |

> 迷ったら Workflow を使う。エージェント間の往復対話が本質的に要る時だけ /team-run。

## コンテキスト保護の鉄則（CRITICAL）

| 禁止 | 理由 |
|------|------|
| メインセッションが implementer/reviewer を直接 `Agent()` 呼び出し | 出力がメインコンテキストを汚染する |
| `Agent()` の返り値に生コード・差分・ログを含める | 同上 |
| メインセッションが Codex を直接呼ぶ | orchestrator サブエージェントの責務 |
| schema なしで Agent() を呼ぶ | 返り値を compact JSON に絞れない |

## フロー

### Phase 1: 計画（メインセッション担当）

1. **編成**: `TeamCreate({team_name: <タスクのkebab>, agent_type: "team-lead"})`

2. **planner 起動（compact 出力）**:
   planner を `schema` 付きで起動し、返り値を構造化 JSON に限定する。
   planner への指示に必ず含める:
   - タスクを最大10件に分解し `blockedBy` で依存を表す
   - 出力は schema 準拠の JSON のみ（説明文・コードブロック禁止）
   - `codexRequired: true` は「3ファイル以上 or 複雑な実装」に付ける

   ```
   PLAN_SCHEMA = {
     summary: string (≤200字),
     tasks: [{ id, title, type: explore|implement|review|test,
               description (≤300字), blockedBy: string[],
               codexRequired: boolean }],
     risks: string[]
   }
   ```

3. **人間ゲート（CRITICAL）**: planner 完了後、メインセッションは以下を実施
   1. PLAN_SCHEMA を整形してチャットに提示（`mcp__visualize__show_widget` で図示可）
   2. `AskUserQuestion` で承認を取得:
      - **承認** → Phase 2 へ進む
      - **修正要求** → planner を再起動して計画修正 → 再提示（最大2回）
      - **却下** → team に shutdown を通知して終了
   3. 承認なしに Phase 2 を起動してはならない

### Phase 2: 実装（orchestrator サブエージェントに完全委任）

4. **orchestrator サブエージェントを起動**:
   承認済みの plan JSON を prompt に含め、`subagent_type: "orchestrator"` で起動。
   schema で返り値を REPORT_SCHEMA に絞る。

   ```
   REPORT_SCHEMA = {
     status: SHIP | NEEDS_WORK | BLOCKED,
     changedFiles: string[],
     reviewFindings: [{ severity: CRITICAL|IMPORTANT|MINOR, message: string }],
     blockers: string[]
   }
   ```

   orchestrator サブエージェントの全責務（メインセッションは実行しない）:
   - `TaskCreate` でタスクリスト登録（blockedBy を依存として使う）
   - `implementer` 起動 → 内部で必ず `codex:codex-rescue` に委任（codexRequired=true のタスク）
   - `reviewer` 起動（arch/security/perf 等の専門エージェント）
   - 品質ゲート（CRITICAL/IMPORTANT がなくなるまでループ、差し戻し最大3回）
   - 各 teammate に `SendMessage({type: "shutdown_request"})`

5. **報告**: REPORT_SCHEMA を整形してチャットに出力

## orchestrator サブエージェント内のルール

- **実装は原則 Codex**: `codexRequired=true` のタスクは必ず `codex:codex-rescue` に委任。Claude 実装は1-2ファイルの軽微な変更のみ許容
- **orchestrator 自身はコードを書かない**: 調整・判定・委任のみ
- **レビューアーは専門エージェントを使う**: `arch-reviewer` / `security-reviewer` / `perf-reviewer` 等
- **CRITICAL 指摘は必ず修正**: 3回で解消しなければ NEEDS_WORK で報告
- **コンテキストが重くなったら**: 長大な差分・ログは読まず、ファイルパスと変更サマリーのみで判断

## 安全・制約

- 外部書き込み（PR/Jira/Slack）は冪等に（既存検索→更新 or 新規）
- teammate 数は4目安、差し戻しは最大3回（無限ループ防止）
- teammate が idle でも慌てない（idle=入力待ち。メッセージで起こせる）
- `teams/` 配下に実行時状態が生成される（完了後は整理）

## 参照

- `agents/orchestrator.md` — orchestrator サブエージェントの役割定義
- `context/loop-engineering.md` — 実行モデルの正典
- `skills/autonomous-loops/SKILL.md` — DAG/PRループのパターン
