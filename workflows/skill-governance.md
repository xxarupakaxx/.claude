# Skill Governance Workflow

これは Claude Workflow Tool の executable `.js` ではない。Agent と人間が共有する durable policy artifact である。

## Trigger

- 外部 Agent Skill の導入、比較、評判調査。
- installed Skill の provenance、update、collision、retirement。
- `skill-stocktake` からの read-only estate audit。

## Context brief

- Goal: 候補 catalog を広く、active runtime を小さく審査済みに保つ。
- Authority: Codex registry。Claude は同一 generation の replica。
- Default capability: local read-only、offline。
- Non-goals: auto-install、auto-update、auto-retire、delete、candidate code execution。

## Required flow

```text
audit authority/parity
  -> discover metadata
  -> verify complete pinned source tree
  -> quarantine outside runtime as source/full-sha/skill
  -> verify complete upstream package Git tree + hash all captured files with FD-anchored traversal
  -> recompute static inspection over the exact quarantine tree
  -> create target-specific review stage outside runtime
  -> inspect instructions/code/dependencies/license + bind full YAML receipts
  -> evaluate value against baseline
  -> bind catalog provenance + adaptation diff + safety/value receipts to the exact subject
  -> bind human approval to both receipt digests
  -> path-scoped promotion
  -> verify + commit each runtime
  -> prove each origin/main with delivery --live
  -> notify-only update monitoring
```

## Checkpoints

1. Authority Gate: registry-lock binding と replica parity が green。
2. Identity Gate: canonical source、full commit SHA、root tree hash、complete package tree SHAがあり、`catalog --live` が全 `SKILL.md` path / blob SHAと各package directory tree SHAを照合する。
3. Safety Gate: catalog path / blob / package tree、quarantine / review manifest、license evidence、surface-bound full YAML receipts、machine-recomputed static inspection、全target hash、adaptation artifact、安全審査receiptが同じsubjectへbindされ、blocking finding が0。scanner pass 単独は不可。
4. Value Gate: subject-bound value receipt が baseline 改善を示す。
5. Human Gate: human approval receipt が同じsubjectとsafety / value receipt hashへbindする。
6. Promotion Gate: safety reviewが期限内で、promotion receiptのquarantine / approved / pre / post hashが同一subjectへbindされ、reviewとruntimeのhashが同一。`update-available`と`deprecated`でもlineageを維持する。
7. Delivery Gate: 両repoが同じgenerationで、scoped pathがclean、各origin/mainがlocal HEADと一致する。片側失敗は `DEGRADED`。

## Push-right policy

- upstream update、権限拡大、新 domain、新 dependency、新 script は reviewer と人間へ push right する。
- L2 capability、license 不明、mutable external instruction は既定 NO-GO。
- `legacy-active` は integrity baseline だけを持つ。approval済みと表示しない。
- retire は非破壊な state change を先に行い、delete は別承認にする。
- 非runtime stateの露出、capture不一致、YAML / JSON解釈差、固定remote URL不一致はBLOCKINGとする。

## Handoff brief

- candidate ID、source、commit、tree hash。
- state、risk tier、blocking / advisory findings。
- safety receipt、value receipt、未解消 evidence gap。
- target roots、adapter差分、collision。
- requested approval と rollback。
