---
name: graph-engineering
description: "複数のloopをnode、edge、typed shared state、単一writer、独立checkerで統治するuser-invoked workflow。fan-out/fan-in、auditable routing、checkpoint、failure isolation、異なる権限が本当に必要なjobだけに使う。"
---

# /graph-engineering

Graph Engineering contract を検証し、既存の `team-run` と session-provided collaboration capability の上で job 全体を統治する。

## 起動権

user-invoked。ユーザーが Graph Engineering、複数 loop の coordination、またはこの skill を明示した場合だけ起動する。

## 最初に読む

1. `context/workflow-rules.md`
2. `context/graph-engineering.md`
3. `context/agent-team-routing.md`
4. `commands/team-run.md`
5. `context/team-run.md`

project override がある場合は、その後に project の `CLAUDE.md` と `.claude/context/` を重ねる。

## Gate 0: graph が必要か

`context/graph-engineering.md` の Adoption boundary を確認する。

単一 loop または checklist で合格基準を満たせる場合は、graph を作らず `team-run` または単一 session を提案して止める。複雑さを graph 採用理由にしない。

## Gate 1: contract

`templates/graph-engineering/graph-contract.example.json` を基に、task memory 内へ `graph-contract.json` を作る。

contract には次だけを置く。

- 実在する specialty / gate に対応する node
- routing owner が一意な edge
- scope、writer、provenance を持つ state field
- loop brake
- external side effect がある場合の safety contract

Wayfinder map、Team Journal、会話全文、artifact 本文は複製せず参照する。

次を実行し、PASS 前に node を起動しない。

```bash
python3 scripts/validate-graph-contract.py <task-memory>/graph-contract.json
```

## Gate 2: run

1. Goal、Sprint Contract、Outcome Trace を `team-run` の規則で固定する。
2. predecessor が完了し、edge condition を満たした node だけを frontier にする。
3. Delegation Gate を通る node だけを委任する。通らない node は lead が逐次実行する。
4. maker の write scope は重複させず、artifact writer は一人に固定する。
5. checker / judge は artifact に対して read-only とし、fresh context と外部証拠で判定する。判定結果は contract で割り当てた run state field にだけ書く。
6. node 完了ごとに `templates/graph-engineering/graph-run.md` 形式の receipt を記録する。
7. deterministic edge は code、test result、明示 state で判定する。model / human routing は contract に記載された場合だけ使う。
8. loop は `max_iterations` と node budget を消費する。上限到達時は別 edge を推測せず停止する。

## Replay

checkpoint から再開する前に、再実行される node を列挙する。

- `side_effect: none`: receipt と artifact freshness を確認して再実行できる。
- `side_effect: external`: approval、idempotency key、target resolution を再確認する。
- 書き込み済みか不明な外部 node は再実行せず、人間へ escalate する。

## Exit gate

次のすべてを満たすまで job 完了にしない。

- terminal node が完了している
- Sprint Contract に未達がない
- Outcome Trace に unmatched outcome がない
- CRITICAL / IMPORTANT review finding が 0
- external side effect receipt に対象と承認参照がある
- holistic check が PASS

完了報告では、contract path、実行済み node、loop 回数、routing decision、state / artifact reference、検証 evidence、未実行 edge を示す。
