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

各 stage は local-first の後、`context/agent-team-routing.md` の Delegation Gate を通る場合だけ委任する。capability がなければ lead が同じ handoff と acceptance を保って逐次実行する。

1. **コンテキスト注入**: タスク説明 + 前のエージェントのハンドオフドキュメント
2. **stage 実行**: 利用可能な session-provided capability で、role、read / write scope、acceptance を明示して実行する
3. **ハンドオフ生成**: 結果を構造化ドキュメントとして整理
4. **次のエージェントへ引き継ぎ**

外部書き込みは `context/agent-team-routing.md` の External Write Gate を通す。作成または更新の前に既存 artifact を確認し、target、operation、結果を handoff と 05_log.md に残す。

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

## オーケストレーション機構の使い分け

| 責務 | 性質 | 使う場面 |
|------|------|---------|
| direct sequential | lead が同じ文脈で実行 | 小さく閉じる、または Gate を通らない作業 |
| available short fan-out | 利用可能な capability による独立・短命の調査、比較、review | 並列利益があり、read / write scope が独立する場合 |
| **`/team-run`** | Goal、Team Journal、Review Heat を共有する協調 overlay | 複数ターンの共有状態が本質の場合 |
| **`/orchestrate`** (本コマンド) | handoff 文書を残す固定順序の stage chain | 順序が重要で、各 handoff を検査したい場合 |
| **`/lfg`** | Phase 0-5.5 の全フェーズを自律チェーン実行 | 1タスクを最初から最後まで通す（包括的） |
| **`blueprint`** | 多セッション・多PRの設計図生成 | 大規模・長期タスクの分解 |

> 選択の正本は `context/agent-team-routing.md` と `context/team-run.md`。`/orchestrate` は `/lfg` のPhase内で部分的に使うことも、独立して使うことも可能。

## 並列実行

Delegation Gate を通り、read / write scope が重ならない独立 stage だけを、利用可能な capability で並列起動できる。capability がなければ順次実行する。例:
- `feature`の`test-reviewer` + `security-reviewer`は並列実行
- `security`の初回スキャンと修正は順次実行

## 注意事項

- 各エージェントのハンドオフは05_log.mdにも記録する
- チェーン中にブロッカーが出たら中断してユーザーに報告
- エージェント名は `~/.claude/agents/` 配下の定義に準拠
