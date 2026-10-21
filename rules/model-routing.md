# Model Routing Rules

Claude Code から Agent Tool でサブエージェントを起動する際のモデル選択ルール。

## 基本方針

通常は `model` を省略し、親セッションのモデルを継承させる。
明示的な指定は、Cost Ladder で lane を固定する必要がある場合だけ使う。
plugin / skill / agent role の選択は `context/agent-team-routing.md` を参照する。このファイルは model 方針に集中する。

## 推論量と文脈の使い方

モデル・effortの既存設定を維持する。新規セッションで`~/.claude/bin/claude-optimized`を使うと、CLIのネイティブflagで可変の環境情報をsystem promptから最初のuser messageへ分ける。`--system-prompt`指定時は無視され、通常の`claude`や既存セッションには自動適用しない。

- 固定の共通指示とtool定義を安定させ、作業path・時刻・差分などの可変情報は作業入力へ置く。必要なSkillの指示は保持し、無関係なSkill一覧を毎回追加しない。
- 必要な参照先が分かる場合は最初に渡し、独立した検索・読込を出力量の範囲内でまとめる。保存済み原典と同じ版の資料を再利用し、変更があれば該当箇所と依存を読み直す。
- effortとモデルは作業開始時に選ぶ。重要判断・セキュリティ・最終レビューの品質を下げず、セッション途中の不要な切替でキャッシュを壊さない。
- timeoutとproviderの失敗を区別し、有限のtimeout・retryとその理由を記録する。cancel時は停止手段のある子処理も止め、残った処理は明記する。完了条件を満たした後に新しい目的のない追加turnを作らない。

起動方法と効果の確かめ方は[推論最適化の手引き](../context/inference-optimization.md)を参照する。

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
| 戦略相談・セカンドオピニオン（外部・on-demand） | shell: `scripts/consult-gpt.sh`（`skills/consult-gpt/SKILL.md` 参照） | gpt-5.5（codex CLI経由・Cost Ladder外） |

## Cost Ladder

| Level | 使う場面 | 例 | 昇格条件 |
|---|---|---|---|
| L0 local | 機械的な処理で完結する | Grep、Glob、diff確認、format check、実際のgit操作 | 要約や判断が必要 |
| L1 haiku | 短く低リスクで、leadがすぐ検査できる | commit文案、短いログ要約、定型整形、重複検出 | 不確実性、矛盾、複数ファイル判断、ユーザー影響 |
| L2 sonnet | 探索、routine実装、通常ワーカー | コードベース調査、既知パターンの実装、軽量な複数ファイル作業 | 重要設計、CRITICALまたはIMPORTANT、高リスク |
| L3 opus | 失敗コストが高い判断 | 計画、GO/NO-GO、セキュリティ、専門レビュー | 独立審判または人間判断が必要 |

### `haiku` を使ってよい条件

- 入力が短く、成果物を lead がすぐ検査できる。
- 変更を書かない、または書く場合でも単一の低リスク text artifact に閉じる。
- 失敗時のコストが低く、再実行や lead 修正が容易。
- 例: git-cz 日本語 commit message 候補、短い調査ログ要約、明確なテンプレートへの整形、重複 URL / 見出しの検出。

### `haiku` を使わない条件

- セキュリティ、認証、課金、データ削除、外部書き込み、GO/NO-GO 判定。
- 3ファイル以上の実装、未知コードの設計判断、レビューの最終判定。
- ユーザー要件が曖昧、ソース間に矛盾がある、引用や法務・医療・金融など高リスク根拠が必要。
- 既存の専門 role で表現できる作業。role 既定を override しない。

不確実性、矛盾、複数ファイル判断、外部副作用が出たら、その round を止めて `sonnet` または `opus` へ昇格する。

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

| teammate | subagent_type | model | 責務 |
|----------|--------------|-------|------|
| planner  | Plan / `implementation-planner` | **opus** | 分解、依存関係、合格基準案、リスク |
| plan-reviewer | `arch-reviewer` / `technical-evaluator` | **opus** | YAGNI、依存矛盾、実現可能性のレビュー |
| explorer | Explore | **sonnet** | 検索ファーストのコードベース調査 |
| implementer | implementer | **sonnet** | disjoint な write scope 内の実装 |
| reviewer | arch-reviewer 等 | **opus** | 成果物ベースの独立レビュー |

## Workflow内のmodel指定

Workflow Tool の `agent()` 関数では `model` オプションで上書き可能:
- `agent('...', { model: 'opus' })` — 判定・レビュー用
- `agent('...', { model: 'sonnet' })` — routine実装用
- `agent('...', { model: 'haiku' })` — commit文案・短い要約・定型整形用
- `agent('...')` — model省略で親セッション継承

## External Consult（外部相談段・Cost Ladder の外）

Cost Ladder（L0-L3）の上に、外部モデルへの単発セカンドオピニオン相談がある。

- 経路: `consult-gpt` スキル → `scripts/consult-gpt.sh` → codex CLI（`codex exec`、読み取り専用サンドボックス）。shell 実行であり Agent ツールでは呼ばない。
- 実装の委任は従来どおり `codex:codex-rescue`。consult-gpt は意見だけ聞くチャネルで、作業の所有権は移らない。
- 昇格条件・1往復原則・セキュリティ境界の SSoT は `skills/consult-gpt/SKILL.md`。
- hot path に入れない: 毎ターンの常設段にしない。日次上限ガードあり。

## 注意

- 迷ったら model を省略する
- `haiku` は reviewer の代替にしない
- commit作業全体をagentへ渡さず、文案だけを必要時に委任する
- Adversarial Review（Red/Blue/Auditor）のモデル割り当ては `adversarial-review` スキルの定義に従う
- Tier 1-3レビューアーは各 `agents/*.md` の定義で品質を担保する
- バージョン付きモデル名（Fable 5 / Opus 4.8 等）の扱いと Fable 5 固有の effort 指針は `skills/prompting-fable` を参照
