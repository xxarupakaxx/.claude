---
name: orchestrate
description: "エージェントチェーンを順次実行するオーケストレーター。feature/bugfix/refactor/security等のワークフロー種別に応じて、専門エージェントをハンドオフドキュメント付きでチェーン実行する。"
---

# エージェントオーケストレーション

## 概要

タスク種別に応じた専門エージェントチェーンを順次実行する。
各エージェントは構造化されたハンドオフドキュメントで次のエージェントに引き継ぐ。

## 使い方

```
/orchestrate <workflow-type> "<タスク説明>"
```

## ワークフロー種別

### `feature` — 新機能開発
チェーン: `requirement-parser` → `implementation-planner` → 実装 → `test-reviewer` → `security-reviewer`

### `bugfix` — バグ修正
チェーン: `data-flow-tracer`（原因調査） → 修正実装 → `test-reviewer`

### `refactor` — リファクタリング
チェーン: `architecture-explorer` → `arch-reviewer`（改善提案） → 実装 → `code-quality-reviewer`

### `security` — セキュリティ強化
チェーン: `security-reviewer`（脆弱性スキャン） → 修正実装 → `security-reviewer`（再検証）

### `custom` — カスタムチェーン
```
/orchestrate custom "agent1,agent2,agent3" "タスク説明"
```

## 実行フロー

各エージェントに対して:

1. **コンテキスト注入**: タスク説明 + 前のエージェントのハンドオフドキュメント
2. **エージェント実行**: Agentツール（subagent_type指定）で実行
3. **ハンドオフ生成**: 結果を構造化ドキュメントとして整理
4. **次のエージェントへ引き継ぎ**

## ハンドオフドキュメント形式

各エージェント間で以下の形式で情報を引き継ぐ:

```markdown
## HANDOFF: [前のエージェント] → [次のエージェント]

### Context
[実行した内容の要約]

### Findings
[発見事項・判断・決定事項]

### Files Modified
[変更したファイルのリスト（パス付き）]

### Open Questions
[未解決の事項・次のエージェントへの質問]

### Recommendations
[推奨される次のステップ]
```

## 最終レポート形式

全エージェント完了後に以下を生成:

```markdown
# ORCHESTRATION REPORT

## Overview
- **Workflow**: [種別]
- **Task**: [タスク説明]
- **Agents**: [チェーン]

## Summary
[1段落の要約]

## Agent Outputs
### [Agent 1]
[要約]
### [Agent 2]
[要約]
...

## Files Changed
[全変更ファイルリスト]

## Test Results
[テスト結果サマリー]

## Recommendation
[SHIP / NEEDS WORK / BLOCKED]
```

## 既存ワークフローとの関係

- **`/lfg`**: Phase 0-5.5の全フェーズ実行（包括的）
- **`/orchestrate`**: 特定の観点でエージェントチェーンを実行（焦点的）

`/orchestrate`は`/lfg`のPhase内で部分的に使うことも、独立して使うことも可能。

## 並列実行

独立したエージェントは並列起動可能。例:
- `feature`の`test-reviewer` + `security-reviewer`は並列実行
- `security`の初回スキャンと修正は順次実行

## 注意事項

- 各エージェントのハンドオフは05_log.mdにも記録する
- チェーン中にブロッカーが出たら中断してユーザーに報告
- エージェント名は `~/.claude/agents/` 配下の定義に準拠
