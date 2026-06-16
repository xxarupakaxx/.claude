# Loop Engineering System — リファレンスドキュメント

> 自律的な開発・レビューループを実現するClaude Code設定群の全体像。
> このドキュメント単体でシステムの理解・セットアップ・運用が可能。

## アーキテクチャ概要

```
┌─────────────────────────────────────────────────────┐
│                  Scheduled Tasks                     │
│  morning-kickoff(9:00) │ hour-calnedar(毎時)        │
│  jira-spec-poll(毎時)  │ evening-review(18:00)      │
└──────────┬──────────────┬──────────────┬────────────┘
           │              │              │
           ▼              ▼              ▼
┌──────────────────────────────────────────────────────┐
│                    Workflows                          │
│  morning-kickoff.js  │ implementation-drive.js       │
│  tournament-ab.js    │ evening-review.js             │
└──────────┬──────────────┬──────────────┬─────────────┘
           │              │              │
           ▼              ▼              ▼
┌──────────────────────────────────────────────────────┐
│                  Agent Definitions                    │
│  orchestrator │ implementer │ cost-monitor            │
│  daily-planner │ minutes-classifier │ jira-spec-writer│
│  ab-judge │ harness-improver                         │
└──────────┬──────────────┬──────────────┬─────────────┘
           │              │              │
           ▼              ▼              ▼
┌──────────────────────────────────────────────────────┐
│                  Infrastructure                       │
│  Hooks: post-cost-track / stop-harness-improve       │
│  Commands: /loop-status                              │
│  Settings: PostToolUse + Stop hook entries            │
└──────────────────────────────────────────────────────┘
```

## エージェント一覧（4点契約）

### orchestrator
| 項目 | 内容 |
|------|------|
| **目的** | ワークフロー全体制御、タスク分解、適切なエージェントへの委任 |
| **出力形式** | Orchestration Report（委任先・理由・結果のJSON構造） |
| **ツール** | Agent, Workflow, Read, Grep, Glob, Bash, Write, Edit, TaskCreate, TaskUpdate |
| **境界** | 直接コード編集しない。実装はimplementerに委任 |
| **モデル** | opus |

### implementer
| 項目 | 内容 |
|------|------|
| **目的** | コード実装（implement → verify → fix ループ、最大3回） |
| **出力形式** | 変更ファイル一覧 + テスト結果 + 差分サマリー |
| **ツール** | Read, Edit, Write, Bash, Agent(codex/cursor) |
| **境界** | 自分のworktree内のみ。他worktreeへの書き込み禁止 |
| **モデル** | sonnet |

### cost-monitor
| 項目 | 内容 |
|------|------|
| **目的** | トークン使用量追跡、コスト見積もり、閾値超過アラート |
| **出力形式** | CostReport JSON（date, total_cost_usd, breakdown, alert_level, recommendations） |
| **ツール** | Read, Bash(ccusage), Grep |
| **境界** | 読み取り専用。設定変更の提案のみ（実行しない） |
| **モデル** | sonnet |

### minutes-classifier
| 項目 | 内容 |
|------|------|
| **目的** | 議事録アクション項目をAIタスク/人間タスク/情報に分類 |
| **出力形式** | 分類結果JSON（items[].type: auto_execute/human_action/info_only） |
| **ツール** | Read, Grep, Write, Bash |
| **境界** | 曖昧なものはhuman_actionに分類（安全側）。金額・契約・人事は必ずhuman_action |
| **モデル** | sonnet |

### jira-spec-writer
| 項目 | 内容 |
|------|------|
| **目的** | Jiraチケットから仕様書ドラフトを生成 |
| **出力形式** | Markdown仕様書（概要/要件/技術設計/テスト計画/リスク/サブタスク） |
| **ツール** | Read, Grep, Glob, Write, Bash, WebSearch（Jira/Confluence MCPはToolSearch経由で利用可能） |
| **境界** | ドラフトのみ生成（レビュー前マーク）。既存仕様書は上書きしない |
| **モデル** | opus |

### ab-judge
| 項目 | 内容 |
|------|------|
| **目的** | A/B実装の品質比較、3人独立ジャッジによる匿名評価 |
| **出力形式** | Verdict JSON（winner, confidence, scores, reasoning, notable_differences） |
| **ツール** | Read, Grep, Bash(test/lint) |
| **境界** | 評価のみ。コード修正しない。セキュリティスコア2以下は勝者にしない |
| **モデル** | opus |

### harness-improver
| 項目 | 内容 |
|------|------|
| **目的** | 失敗パターン分析 → CLAUDE.md/rules改善提案の生成 |
| **出力形式** | 改善提案（パターン/根拠/提案ルール/適用先） |
| **ツール** | Read, Grep, Glob, Write |
| **境界** | 提案のみ（自動適用しない）。1セッション最大3件。既存ルールとの矛盾チェック必須 |
| **モデル** | opus |

### daily-planner
| 項目 | 内容 |
|------|------|
| **目的** | Jira/Calendar/未完了タスク/PRレビューから優先順位付き日次計画を作成 |
| **出力形式** | DailyPlan JSON（focus, p0[], p1[], p2[], meetings[], carryover[], estimated_hours） |
| **ツール** | Read, Grep, Bash, Write |
| **境界** | 計画作成のみ。タスク実行しない。最大8時間分。P0が3件以上なら確認を要求 |
| **モデル** | sonnet |

## ワークフロー実行フロー

### tournament-ab.js
```
args: {task, spec, testCmd?, baseFile?}

Implement ──→ parallel([plan-a(worktree), plan-b(worktree)])
    │
Test ──────→ parallel([test-a, test-b])
    │
Judge ─────→ parallel([judge-correctness(opus), judge-maintainability(opus), judge-performance(opus)])
    │
Decide ────→ 多数決 + 加重スコア平均 → winner(A/B/tie)
```

### morning-kickoff.js
```
Gather ──→ parallel([jira-tickets, calendar-events, carryover-tasks, pr-reviews])
    │
Plan ────→ daily-planner(opus) → DailyPlan JSON
    │
Notify ──→ Slack投稿
```

### implementation-drive.js
```
args: {ticketKey, useTournament?}

Analyze ──→ チケット分析 → complexity(simple/medium/complex)
    │
Spec ─────→ jira-spec-writer(opus) → 仕様書ドラフト
    │
Implement ─→ simple: 直接実装(worktree)
             medium: pipeline(subtasks, impl→test→review)
             complex/tournament: workflow('tournament-ab', ...)
    │
Verify ───→ テスト + lint + typecheck + コードレビュー
    │
Report ───→ Jiraコメントに記録
```

### evening-review.js
```
Cost ─────→ cost-monitor → CostReport(alert_level)
    │
Failures ─→ harness-improver → FailurePatterns
    │
Improve ──→ [alert≥warning] → モデルダウングレード提案
             [failures.high≥1] → ルール改善提案
    │
Summary ──→ Slack日次サマリー投稿
```

## スケジュールタスク一覧

| タスク | 間隔 | 内容 | ワークフロー |
|--------|------|------|-------------|
| `morning-kickoff` | 毎朝9:00 | 日次計画作成→Slack通知 | morning-kickoff.js |
| `hour-calnedar` | 毎時 | 議事録要約 + アクション分類→自動実行/dailyノート | — (直接実行) |
| `jira-spec-poll` | 毎時 | 新規チケット検出→仕様書ドラフト生成 | — (直接実行) |
| `evening-review` | 毎夕18:00 | コスト/失敗分析→改善提案→Slackサマリー | evening-review.js |

## Hook定義

| Hook | トリガー | 内容 |
|------|---------|------|
| `post-cost-track.sh` | PostToolUse(Bash\|Agent) | ツール呼び出しを日次ログに記録 |
| `stop-harness-improve.sh` | Stop | セッション終了時に失敗パターンを検出→候補ファイル保存 |

## コマンド

| コマンド | 説明 |
|---------|------|
| `/loop-status` | 全ループの状態表示（スケジュールタスク/ワークフロー/コスト/改善提案） |

## マルチモデルディスパッチ

| ロール | モデル | 呼び出し方法 |
|--------|--------|-------------|
| Orchestrator / Judge | claude-opus-4-6 | agent() model:"opus" |
| Standard Worker | claude-sonnet-4-6 | agent() デフォルト |
| Codex実装 | gpt-5.4 | Agent(subagent_type:"codex:codex-rescue") |
| Cursor設計レビュー | gpt-5.5-high | Agent(subagent_type:"cursor:cursor-rescue") |

## ファイル配置

```
~/.claude/
├── agents/                         # エージェント定義
│   ├── orchestrator.md
│   ├── implementer.md
│   ├── cost-monitor.md
│   ├── minutes-classifier.md
│   ├── jira-spec-writer.md
│   ├── ab-judge.md
│   ├── harness-improver.md
│   └── daily-planner.md
├── workflows/                      # ワークフロースクリプト
│   ├── tournament-ab.js
│   ├── morning-kickoff.js
│   ├── implementation-drive.js
│   └── evening-review.js
├── hooks/                          # フック
│   ├── post-cost-track.sh
│   └── stop-harness-improve.sh
├── commands/                       # コマンド
│   └── loop-status.md
├── scheduled-tasks/                # スケジュールタスク
│   ├── morning-kickoff/SKILL.md
│   ├── hour-calnedar/SKILL.md      # 既存（拡張済み）
│   ├── jira-spec-poll/SKILL.md
│   └── evening-review/SKILL.md
├── context/
│   └── loop-engineering.md         # このファイル
└── settings.json                   # Hook登録済み
```

## セットアップ確認手順

### 1. 前提条件
```bash
# Claude Code CLI
which claude

# GitHub CLI
gh auth status

# Codex CLI（オプション）
which codex

# Cursor Agent（オプション）
which cursor-agent
```

### 2. ファイル存在確認
```bash
# エージェント定義（8ファイル）
ls ~/.claude/agents/{orchestrator,implementer,cost-monitor,minutes-classifier,jira-spec-writer,ab-judge,harness-improver,daily-planner}.md

# ワークフロー（4ファイル）
ls ~/.claude/workflows/{tournament-ab,morning-kickoff,implementation-drive,evening-review}.js

# フック（2ファイル、実行権限あり）
ls -la ~/.claude/hooks/{post-cost-track,stop-harness-improve}.sh

# スケジュールタスク（4ディレクトリ）
ls ~/.claude/scheduled-tasks/{morning-kickoff,hour-calnedar,jira-spec-poll,evening-review}/SKILL.md

# コマンド
ls ~/.claude/commands/loop-status.md
```

### 3. Settings.json確認
```bash
# PostToolUse に post-cost-track.sh が含まれること
grep "post-cost-track" ~/.claude/settings.json

# Stop に stop-harness-improve.sh が含まれること
grep "stop-harness-improve" ~/.claude/settings.json
```

### 4. 動作確認
```bash
# ループステータス表示
# Claude Code内で /loop-status を実行

# 手動ワークフロー実行テスト
# Claude Code内で以下を実行:
#   Workflow({name: 'morning-kickoff'})
#   Workflow({name: 'evening-review'})
#   Workflow({name: 'tournament-ab', args: {task: 'テスト', spec: 'Hello Worldを出力'}})
```

## コスト管理

### アラート閾値
| レベル | 金額 | アクション |
|--------|------|-----------|
| ok | $0-5 | 通常運用 |
| info | $5-15 | 日報に記載 |
| warning | $15-30 | モデルダウングレード検討 |
| critical | $30+ | 即時対応、opus→sonnetへの切替 |

### コスト追跡データ
- 日次ログ: `~/.claude/.local/cost-track/YYYYMMDD.log`
- 改善提案: `~/.claude/.local/harness-suggestions/YYYYMMDD_HHMMSS.json`

## 安全設計

1. **AIタスク自動実行の安全弁**: 曖昧なアクション項目はhuman_actionに分類（minutes-classifier）
2. **ハーネス改善の承認制**: harness-improverは提案のみ、自動適用しない
3. **コスト暴走防止**: budget.remaining()ガード + post-cost-track hook + evening-reviewのアラート
4. **Worktree分離**: tournament-abの並列実装はisolation:"worktree"で競合を防止
5. **セキュリティ判定**: ab-judgeはセキュリティスコア2以下の実装を勝者にしない
