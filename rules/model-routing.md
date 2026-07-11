# Model Routing Rules

Claude Code から Agent Tool でサブエージェントを起動する際のモデル選択ルール。

## 基本方針

通常は `model` を省略し、親セッションのモデルを継承させる。
明示的な指定は、Cost Ladder で lane を固定する必要がある場合だけ使う。

## Dispatch Table（Source of Truth）

| 用途 | 呼び出し方法 | モデル |
|------|-------------|--------|
| 探索・監視（explore/pr-watch等） | `Agent(model: "sonnet")` | sonnet |
| commit文案・短い要約・定型整形・重複検出 | `Agent(model: "haiku")` | haiku |
| routine実装・通常ワーカー | `Agent(model: "sonnet")` | sonnet |
| 判定・設計判断・計画・レビュー | `Agent(model: "opus")` | opus |
| 重い実装（3+ファイル） | `Agent(subagent_type: "codex:codex-rescue")` | gpt-5.x（Codex側で管理） |
| 専門レビュー | `Agent(subagent_type: "arch-reviewer")` 等 | opus推奨（明示指定） |
| 過去知見検索 | `Agent(subagent_type: "learnings-researcher")` | 継承 |
| Workflowパイプライン | `Workflow({script: ...})` 内の `agent()` | 継承（`model` オプションで上書き可） |

## Cost Ladder

| Level | 使う場面 | 例 | 昇格条件 |
|---|---|---|---|
| L0 local | 機械的な処理で完結する | Grep、Glob、diff確認、format check、実際のgit操作 | 要約や判断が必要 |
| L1 haiku | 短く低リスクで、leadがすぐ検査できる | commit文案、短いログ要約、定型整形、重複検出 | 不確実性、矛盾、複数ファイル判断、ユーザー影響 |
| L2 sonnet | 探索、routine実装、通常ワーカー | コードベース調査、既知パターンの実装、軽量な複数ファイル作業 | 重要設計、CRITICALまたはIMPORTANT、高リスク |
| L3 opus | 失敗コストが高い判断 | 計画、GO/NO-GO、セキュリティ、専門レビュー | 独立審判または人間判断が必要 |

`haiku` は、短い入力と短い出力で完結し、lead が結果をすぐ検査できる作業に限る。
不確実性、矛盾、複数ファイル判断、外部副作用が出たら、その round を止めて `sonnet` または `opus` へ昇格する。
`haiku` を設計者、セキュリティ reviewer、GO/NO-GO 判定者、最終 reviewer の代わりに使わない。

実際の `git add`、`git commit`、`git push` は shell で実行する。
commit に関して agent へ任せられるのは、メッセージ文案の作成だけである。

## 判断フロー

```
Agent起動時:
  重い実装？ → codex:codex-rescue
  計画・判定・高品質レビュー？ → model: "opus"
  routine実装？ → model: "sonnet"
  探索・監視？ → model: "sonnet"
  短い低リスクhelper？ → model: "haiku"
  それ以外 → model省略（継承）
```

## team-run のモデル割り当て

| teammate | subagent_type | model |
|----------|--------------|-------|
| planner  | Plan | **opus** |
| explorer | Explore | **sonnet** |
| implementer | implementer | **sonnet** |
| reviewer | arch-reviewer 等 | **opus** |

## Workflow内のmodel指定

Workflow Tool の `agent()` 関数では `model` オプションで上書き可能:
- `agent('...', { model: 'opus' })` — 判定・レビュー用
- `agent('...', { model: 'sonnet' })` — routine実装用
- `agent('...', { model: 'haiku' })` — commit文案・短い要約・定型整形用
- `agent('...')` — model省略で親セッション継承

## 注意

- 迷ったら model を省略する
- `haiku` は reviewer の代替にしない
- commit作業全体をagentへ渡さず、文案だけを必要時に委任する
- Adversarial Review（Red/Blue/Auditor）のモデル割り当ては `adversarial-review` スキルの定義に従う
- Tier 1-3レビューアーは各 `agents/*.md` の定義で品質を担保する
- バージョン付きモデル名（Fable 5 / Opus 4.8 等）の扱いと Fable 5 固有の effort 指針は `skills/prompting-fable` を参照
