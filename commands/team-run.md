---
name: team-run
description: "Goal、Team Journal、Review Heat が有用な高価値・複数ターン作業を協調する user-invoked overlay。固定 roster ではなく、Delegation Gate を通る役割だけを追加する。"
---

# /team-run

`/team-run` は作業量だけで Agent Team を作らない。
route と acceptance が明確で、Goal、Team Journal、Review Heat、共有協調が実益を持つときだけ使う。

## 最初に読む正本

1. project の `CLAUDE.md` / `AGENTS.md`
2. `context/workflow-rules.md`
3. `context/agent-team-routing.md`
4. `context/team-run.md`
5. project 固有の `.claude/context/team-run.md`（あれば）

project 固有設定は通知先、実装制約、review 観点を追加できる。
Phase順序、Delegation Gate、外部書き込みの承認、Goal / Contract / Trace の定義は global SSoT を上書きしない。

## 開始判定

| 状況 | 選択 |
|---|---|
| route が霧に包まれ、複数 session にまたがる | `mapping-large-projects` を提案し、まず decision map を作る |
| route が明確で小さく閉じる | direct lane。team-run は使わない |
| 独立作業、隔離された専門知識、独立検証の価値がある | `context/team-run.md` に従い team-run を開始できる |
| capability がない、または Delegation Gate を通らない | lead が逐次実行する |

Agent Teams、Workflow、`Agent()` のどれを使うかは、現在の session が提供する capability と task の協調需要で選ぶ。
feature flag や API 名を仮定しない。

## 実行

1. Phase 0-2 を満たし、Goal Quality Gate を通った active Goal を作る。Sprint Contract は自明な作業だけ、代替検証と省略理由を Team Journal に記録して省略できる。active Goal を使う team-run では Outcome Trace を必ず作る。
2. Team Journal に lane、Gate の判定、選んだ capability、Review Heat、役割と省略理由、Contract の代替検証を記録する。
3. lead だけが役割の作成、task の割当、write scope の変更を決める。planner、explorer、maker、checker、judge は固定ではなく、Delegation Gate を通る役割だけを、objective、scope、acceptance、prior failure、出力形式とともに追加する。
4. 同一ファイルの writer を並列化しない。maker の自己申告では完了にせず、必要な checker は成果物と fresh evidence を見る。
5. Phase 4 では、direct validation を先に行い、Review Heat に合う最小の independent checker または human gate を実行する。
6. Goal の Done、Outcome Trace の未対応0、holistic check、CRITICAL=0、修正済みまたは理由とリスクを記録した IMPORTANT、Team Journal の最終状態を確認して終了する。

外部投稿、tracker 更新、branch / commit / push、secret 操作は team-run の開始だけでは許可されない。
`context/agent-team-routing.md` の External Write Gate と project policy に従う。create / update の前に既存 artifact を検索し、target、operation、結果 URL（または既存更新）を Team Journal に記録して重複作成を防ぐ。

## Orchestration Report

```md
## Orchestration Report
- Status: SHIP | NEEDS_WORK | BLOCKED
- Goal: ...
- Lane / capability: ...
- Outcome Trace: unmatched _ / holistic PASS|FAIL
- Verification: ...
- Review Heat / findings: ...
- Changed Files: [...]
- Blockers / residual risk: ...
```

同じ blocker が3回続く、または material な scope 変更が必要なときは、勝手に継続せず human escalation または Goal の blocked 判定を検討する。
