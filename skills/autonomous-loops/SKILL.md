---
name: autonomous-loops
description: "自律ループパターン集。シーケンシャルパイプライン、PRループ（作成→レビュー→修正→再レビュー）、DAGオーケストレーション（依存グラフに基づく並列実行）の3パターン。"
---

# Autonomous Loops — 自律ループパターン

## 概要

エージェントが自律的に繰り返し実行するための3つのパターンを定義。
`/orchestrate`や`agent-teams`と組み合わせて使用。

## パターン1: シーケンシャルパイプライン

タスクを段階的に処理。各ステップの出力が次の入力になる。

```
[Step 1] → output1 → [Step 2] → output2 → [Step 3] → 最終結果
```

**使用場面**: `/orchestrate`のworkflow実行
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

**使用場面**: `auto-reviewing-pre-pr`の拡張
**ゲート条件**: CRITICAL/IMPORTANT指摘が0件

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

**使用場面**: `blueprint`の依存グラフの実行、`agent-teams`との組み合わせ

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

- **最大ループ回数**: 設定可能（デフォルト: 5）
- **タイムアウト**: 各ステップに上限設定
- **失敗エスカレーション**: 連続失敗でユーザーに報告
- **LLM連続修正上限**: 3回（workflow-rules.md準拠）
- **checkpoint保存**: 各ラウンドでcheckpoint.mdに状態保存
