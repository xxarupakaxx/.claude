# Team Run Policy

`/team-run` のチーム構成、Review Heat、終了判定を定義する。

このファイルは `context/workflow-rules.md` の Phase 0-5.5 を置き換えない。
Phase順序、Goal Quality Gate、Sprint Contract、Outcome Trace、品質確認は `context/workflow-rules.md` が正本である。
ここでは team-run 固有の「チームを作るか」「誰を追加するか」「どこで止めるか」だけを扱う。

## 起動条件

`team-run` は user-invoked の協調 overlay である。
次の条件が揃うときだけ使う。

- route と acceptance が十分に明確である。
- Goal、Team Journal、Review Heat、複数ターンの共有状態が実益を持つ。
- `context/agent-team-routing.md` の Delegation Gate を通る独立作業、隔離された専門知識、または独立検証がある。

route 自体が霧に包まれている場合は `mapping-large-projects` を先に提案する。
route が明確で小さく閉じる場合は direct lane を選ぶ。
Agent Teams や Workflow が使えない、または Gate を通らない場合は lead が逐次実行する。

## Harmony Contract

| 要素 | 役割 | 主な保存先 |
|---|---|---|
| Goal | 価値、Done、停止条件 | active Goal / Team Journal |
| Sprint Contract | 機械判定できる acceptance | `checkpoint.md` / Team Journal |
| Outcome Trace | Goal outcome から evidence までの対応 | `checkpoint.md` / Team Journal |
| Team Journal | 周回をまたぐ決定、状態、失敗原因 | `${MEMORY_DIR}/memory/YYMMDD_<task>/team-journal.md` |
| Review Heat | 変更リスクに対する checker / human gate | このファイル + workflow-rules |

Goal は目的、Sprint Contract は成果物の合格基準、Outcome Trace はその対応である。
Team Journal は現在地であり、完了証明ではない。

## Capability Adapter

| 利用可能な能力 | 使う場面 | 境界 |
|---|---|---|
| Agent Teams | teammate 間の往復対話と共有状態が本質 | lead が役割・scope・acceptance を固定する |
| `Workflow` | 独立した調査、比較、review の短命 fan-out | 同一ファイルの writer を並列化しない |
| `Agent()` | 隔離された専門知識または独立検証 | Delegation Gate を通った task だけ |
| なし | 逐次実行 | Contract と Review Heat を下げない |

API 名や feature flag を前提にしない。
現在の session が提供する能力を確認してから使う。

## Role Selection

| 役割 | 使う条件 | 責務 |
|---|---|---|
| planner | lead の計画だけでは独立した分解が不足する | 依存、acceptance、risk、write scope の整理 |
| explorer | local-first で事実が不足する | 検索ファーストの調査と evidence asset |
| maker | disjoint な write scope がある | 承認済み task の実装 |
| checker | risk に対する独立検証が必要 | 成果物と fresh evidence の確認 |
| judge | GO/NO-GO が lead 単独で裁けない | 残存リスクと出荷可否 |

表は固定 roster ではない。
maker と checker は同一 agent にしない。

lead だけが役割の作成、task の割当、write scope の変更を決める。worker は役割の追加、再割当、外部書き込みを自分で始めず、必要性と対象を lead へ返す。

外部 artifact を create / update する前に、lead は既存 artifact を検索して対象を確定する。Team Journal には target、operation、結果 URL（または「既存を更新」）を記録し、同じ issue、comment、PR、tracker item を重複作成しない。

## Review Heat

| Heat | 使う場面 | 最低限 |
|---|---|---|
| 0 | typo、単一文書、外部影響なし | fresh な lead self-check |
| 1 | 設定・文書・workflow policy | 必要な `docs-reviewer`、`rule-validator`、または human gate |
| 2 | 複数責務の実装 | 変更に対応する最小の independent checker |
| 3 | 権限、外部書き込み、不可逆操作、重要設計 | independent review と必要な human gate |
| 4 | security、契約、ESCALATE | `adversarial-review` または auditor を含む判断 |

ファイル数だけで Heat や reviewer 数を決めない。

## Context Boundary

各 teammate に渡すのは、全文の会話ではなく次だけにする。

- objective
- read / write scope
- acceptance と evidence
- prior failure の原因
- 出力形式と最大量

詳細は Team Journal、05_log.md、durable artifact に残す。
lead への返答は compact summary にし、生の diff や長い log を流さない。

## Lifecycle

1. project の `CLAUDE.md` / `AGENTS.md`、`context/agent-team-routing.md`、このファイル、project 固有 `.claude/context/team-run.md` を読む。
2. Phase 0-2 を満たし、Goal Quality Gate を通った active Goal を作る。Sprint Contract は自明な作業だけ、代替検証と省略理由を Team Journal に記録して省略できる。active Goal を使う team-run では Outcome Trace を必ず作る。
3. Team Journal に lane、Gate の判定、選んだ capability、Review Heat、役割と省略理由、Contract の代替検証を記録する。
4. 依存のない task だけを並列化する。write scope が重なる task は一人の writer に固定する。
5. fresh な直接検証を先に行い、Review Heat に応じた最小の checker または human gate を実行する。
6. Goal の Done、Outcome Trace の未対応0、holistic check、CRITICAL=0、修正済みまたは理由とリスクを記録した IMPORTANT、Team Journal の最終状態を確認して終了する。

同じ blocker が3回続く、validation が同じ理由で3回失敗する、または material な scope 変更が必要な場合は、続行せず human escalation または Goal の blocked 判定を検討する。
