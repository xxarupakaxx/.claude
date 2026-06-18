---
name: autonomous-loops
description: "自律ループパターン集。シーケンシャルパイプライン、PRループ（作成→レビュー→修正→再レビュー）、DAGオーケストレーション（依存グラフに基づく並列実行）の3パターン。"
---

# Autonomous Loops — 自律ループパターン

## 概要

エージェントが自律的に繰り返し実行するための3つのパターンを定義。各パターンは以下の**実体**で実現する（抽象論ではなく既存の実装に紐付く）:

| パターン | 実装機構 |
|---------|---------|
| 1. シーケンシャルパイプライン | `Workflow` tool の `pipeline()` |
| 2. PRループ（レビュー→修正→再レビュー） | `workflows/pr-review-loop.js`（または `auto-reviewing-pre-pr` を手動ループ） |
| 3. DAGオーケストレーション | `Workflow` tool の `parallel()`/`pipeline()`（依存順に段組み）、エージェント間協調が要るなら `/team-run`（Agent Teams） |

## パターン1: シーケンシャルパイプライン

タスクを段階的に処理。各ステップの出力が次の入力になる。

```
[Step 1] → output1 → [Step 2] → output2 → [Step 3] → 最終結果
```

**使用場面**: `Workflow` tool の `pipeline()`（各item をステージ列に流す）
**ゲート条件**: 各ステップ完了後に品質チェック

```markdown
Pipeline: feature-development
Steps:
  1. plan: 設計 → 30_plan.md
  2. implement: 実装 → コード変更
  3. test: テスト → テスト結果
  4. review: レビュー → レビュー結果
Gate: 各ステップでFAILなら前のステップに戻る
Max-Retries: 2
```

## パターン2: PRループ

PR作成→レビュー→修正→再レビューを合格まで繰り返す。

```
[PR作成] → [レビュー] → PASS? → YES → [マージ]
                ↓ NO
            [修正] → [再レビュー] → PASS? → YES → [マージ]
                          ↓ NO
                      [修正] → ... (最大3回)
```

**使用場面**: `workflows/pr-review-loop.js`（並列専門レビュー→自動修正→再レビュー、最大3R）。スケジュールタスク `pr-review` がこれを呼ぶ。PR作成後の**CIステータス＋レビュー継続監視**は `/pr-watch`（`/loop 30m /pr-watch <PR>` で30分おき）が担い、CI失敗の自動修正（`gh pr checks`→失敗ログ→修正→push）を pr-review-loop に上乗せする。
**ゲート条件**: CRITICAL/IMPORTANT指摘が0件 かつ CI全green

```markdown
PR-Loop:
  Create: gh pr create --draft
  Review: auto-reviewing-pre-pr (arch + security + perf)
  Fix: 指摘を修正 + コミット
  Re-Review: サブエージェント再起動
  Pass-Criteria: CRITICAL=0, IMPORTANT=0
  Max-Rounds: 3
  Escalation: 3回で未解決 → ユーザーに報告
```

## パターン3: DAGオーケストレーション

依存グラフに基づいて、並列実行可能なタスクを同時に処理。

```
    [A: Schema] ──→ [B: API] ──→ [D: Frontend]
         ↓                              ↑
    [C: Domain Logic] ─────────────────┘
                                   [E: Tests]
```

**使用場面**: `Workflow` tool で依存順に `parallel()` を段組みする（`blueprint`の依存グラフ実行）。エージェント間の往復協調が要る場合は `/team-run`（Agent Teams）

```markdown
DAG:
  A: {task: "DB Schema", deps: [], parallel: false}
  B: {task: "API Layer", deps: [A], parallel: true}
  C: {task: "Domain Logic", deps: [A], parallel: true}
  D: {task: "Frontend", deps: [B, C], parallel: false}
  E: {task: "E2E Tests", deps: [D], parallel: false}

Execution:
  Round 1: A (単独)
  Round 2: B + C (並列)
  Round 3: D (B,C完了後)
  Round 4: E (D完了後)
```

## 安全ガード（全パターン共通）

- **最大ループ回数**: デフォルト 5（pr-review-loop は 3）。Workflowスクリプト内の `maxRounds` 引数、または `checkpoint.md` の合格基準で制御する
- **タイムアウト**: 各ステップ デフォルト 30 分。orchestrate 設定で上書き可
- **失敗エスカレーション**: 連続 2 回失敗 → AskUserQuestion で人間判断を求める
- **最大ループ超過時**: ESCALATE として残存タスクと進捗を AskUserQuestion でユーザーに報告
- **LLM連続修正上限**: 3 回（workflow-rules.md / auto-reviewing-pre-pr SKILL.md 準拠）
- **checkpoint保存**: 各ラウンド終了時に `checkpoint.md` へ状態保存（再開可能性を担保）
