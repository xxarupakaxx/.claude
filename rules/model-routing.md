# Model Routing Rules

Claude Code から Agent Tool でサブエージェントを起動する際のモデル選択ルール。

## 基本方針

通常は `model` を省略し、親セッションのモデルを継承させる。明示的なモデル指定は特定の用途のみ。

## Dispatch Table（Source of Truth）

| 用途 | 呼び出し方法 | モデル |
|------|-------------|--------|
| 探索・監視（explore/pr-watch等） | `Agent(model: "haiku")` | haiku |
| 軽量ワーカー・実装 | `Agent(model: "sonnet")` | sonnet |
| 判定・設計判断・計画・レビュー | `Agent(model: "opus")` | opus |
| 重い実装（3+ファイル） | `Agent(subagent_type: "codex:codex-rescue")` | gpt-5.x（Codex側で管理） |
| 専門レビュー | `Agent(subagent_type: "arch-reviewer")` 等 | opus推奨（明示指定） |
| 過去知見検索 | `Agent(subagent_type: "learnings-researcher")` | 継承 |
| Workflowパイプライン | `Workflow({script: ...})` 内の `agent()` | 継承（`model` オプションで上書き可） |

## 判断フロー

```
Agent起動時:
  重い実装？ → codex:codex-rescue
  計画・判定・高品質レビュー？ → model: "opus"
  実装（中程度）？ → model: "sonnet"
  探索・監視・軽量タスク？ → model: "haiku"
  それ以外 → model省略（継承）
```

## team-run のモデル割り当て

| teammate | subagent_type | model |
|----------|--------------|-------|
| planner  | Plan | **opus** |
| explorer | Explore | **haiku** |
| implementer | implementer | **sonnet** |
| reviewer | arch-reviewer 等 | **opus** |

## Workflow内のmodel指定

Workflow Tool の `agent()` 関数では `model` オプションで上書き可能:
- `agent('...', { model: 'opus' })` — 判定・レビュー用
- `agent('...', { model: 'sonnet' })` — 軽量タスク用
- `agent('...')` — model省略で親セッション継承

## 注意

- 迷ったら model を省略する
- Adversarial Review（Red/Blue/Auditor）のモデル割り当ては `adversarial-review` スキルの定義に従う
- Tier 1-3レビューアーは各 `agents/*.md` の定義で品質を担保する
- バージョン付きモデル名（Fable 5 / Opus 4.8 等）の扱いと Fable 5 固有の effort 指針は `skills/prompting-fable` を参照
