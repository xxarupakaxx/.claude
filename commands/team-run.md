---
name: team-run
description: "複数エージェントが自律協調するAgent Teamを編成してタスクを遂行する（TeamCreate/SendMessage）。Workflowの単一fan-outでは足りない、エージェント間の対話的協調・複数ターンに渡る協働が必要なタスクに使う。"
---

# /team-run — Agent Team オーケストレーション（柱A: 自律協調）

複数エージェントが共有タスクリストと `SendMessage` で**自律的に協調**しながらタスクを遂行する。
指揮者（team-lead = あなた）が編成・割当・品質ゲートを担う。

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

## フロー

1. **編成**: `TeamCreate({team_name: <タスクのkebab>, agent_type: "team-lead"})`
2. **分解**: タスクを `TaskCreate` で共有タスクリストへ登録（依存は `blockedBy` で表現）
3. **teammate起動**: `Agent({team_name, name, subagent_type})` で役割エージェントを起動
   - `planner` (subagent_type: "Plan") — 設計・調査（読み取り専用）
   - `implementer` (subagent_type: "general-purpose") — 実装。重い実装は `codex:codex-rescue` へ委任
   - `reviewer` (subagent_type: 専門reviewer) — arch/security/perf 等
4. **割当**: `TaskUpdate` で `owner` を割当。teammate は完了→`TaskList`で次を取得→`SendMessage`で連携
5. **品質ゲート**: team-lead は各タスク完了時にレビュー。CRITICAL/IMPORTANTが残れば差し戻し（最大3回）。
   - レビュー→修正ループは `workflows/pr-review-loop.js` を活用してよい
6. **終了**: 全タスク完了 → 各teammateに `SendMessage({type: "shutdown_request"})`
7. **報告**: Orchestration Report を出力（agents/orchestrator.md の形式）

## 安全・制約

- 外部書き込み（PR/Jira/Slack）は冪等に（既存検索→更新 or 新規）
- teammate数は4目安、各タスクの差し戻しは最大3回（無限ループ防止）
- teammateがidleでも慌てない（idle=入力待ち。メッセージで起こせる）
- `teams/` 配下に実行時状態が生成される（完了後は不要なら整理）

## 参照

- `agents/orchestrator.md` — team-lead（指揮者）の役割定義
- `context/loop-engineering.md` — 実行モデルの正典
- `skills/autonomous-loops/SKILL.md` — DAG/PRループのパターン
