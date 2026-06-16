# Model Routing Rules

Claude Code から Agent Tool でサブエージェントを起動する際のモデル選択ルール。

## 基本方針

通常は `model` を省略し、親セッションのモデルを継承させる。明示的なモデル指定は特定の用途のみ。

## Dispatch Table（Source of Truth）

| 用途 | 呼び出し方法 | モデル |
|------|-------------|--------|
| コードベース探索 | `Agent(subagent_type: "Explore")` | sonnet |
| 軽量ワーカー | `Agent(model: "sonnet")` | sonnet |
| 判定・設計判断・レビュー | `Agent(model: "opus")` | opus |
| 重い実装（3+ファイル） | `Agent(subagent_type: "codex:codex-rescue")` | gpt-5.x（Codex側で管理） |
| 専門レビュー | `Agent(subagent_type: "arch-reviewer")` 等 | 継承 |
| 過去知見検索 | `Agent(subagent_type: "learnings-researcher")` | 継承 |
| Workflowパイプライン | `Workflow({script: ...})` 内の `agent()` | 継承（`model` オプションで上書き可） |

## 判断フロー

```
Agent起動時:
  重い実装？ → codex:codex-rescue
  コードベース探索？ → Explore
  判定・高品質レビュー？ → model: "opus"
  軽量タスク？ → model: "sonnet"
  それ以外 → model省略（継承）
```

## Workflow内のmodel指定

Workflow Tool の `agent()` 関数では `model` オプションで上書き可能:
- `agent('...', { model: 'opus' })` — 判定・レビュー用
- `agent('...', { model: 'sonnet' })` — 軽量タスク用
- `agent('...')` — model省略で親セッション継承

## 注意

- 迷ったら model を省略する
- Adversarial Review（Red/Blue/Auditor）のモデル割り当ては `adversarial-review` スキルの定義に従う
- Tier 1-3レビューアーは各 `agents/*.md` の定義で品質を担保する
