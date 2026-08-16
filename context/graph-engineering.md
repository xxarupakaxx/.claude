# Graph Engineering

Graph Engineering は複数の loop を接続・統治する coordination layer である。
新しい scheduler の名前ではなく、既存の `team-run` を明示的な node、edge、shared state、authority で扱うための契約とする。

## Layer boundary

```text
prompt → context → harness → loop → graph
```

| Layer | 作業単位 | この設定での正本 |
|---|---|---|
| Prompt | 1 message | 各 skill / prompt |
| Context | window に残す情報 | handoff artifact / state reference |
| Harness | 1 pass | Claude Code runtime、tools、tests、reviewers |
| Loop | 1 run | `team-run`、Goal、Sprint Contract、Team Journal |
| Graph | job 全体 | graph contract、node receipt、routing decision |

Graph は下位 layer を複製しない。Wayfinder の planning state と team-run の run-local state を正本として保ち、graph state には field owner、scope、provenance と artifact reference だけを持たせる。

## Adoption boundary

次のいずれかが必要な場合だけ graph を使う。

- 独立した specialty の fan-out / fan-in
- 複数 loop 間の auditable routing
- checkpoint と replay
- failure isolation
- node ごとに異なる権限や human gate

単一 loop、逐次 checklist、同じ writer が一続きで行う作業には使わない。node を一つに畳んでも責務・権限・検証が失われないなら、その node は分けない。

## Contract v1

contract は JSON object とし、`templates/graph-engineering/graph-contract.example.json` を executable example とする。

### Top level

| Field | Meaning |
|---|---|
| `version` | 現在は文字列 `"1"` |
| `name` | graph の安定した名前 |
| `entrypoints` | 実行開始 node id の配列 |
| `nodes` | node id を key にした node 定義 |
| `state` | state field 名を key にした field 定義 |
| `edges` | edge 定義の配列 |

### Node

- `kind`: `loop`、`function`、`tool`、`human_gate`
- `role`: `worker`、`checker`、`judge`
- `authority`: `read_only`、`artifact_writer`
- `reads` / `writes`: state field 名の配列
- `side_effect`: `none` または `external`

`authority` は artifact を変更できるかを表す。
`read_only` node も、contract で writer に指定された non-artifact state には書き込める。

`checker` と `judge` は artifact scope を書き換えない。
artifact の writer は一人に固定し、checker は review verdict を別の run state field に書く。

`side_effect: external` の node は `safeguards` に次の三つを持つ。

- `approval`: 誰が何を承認したかへの参照
- `idempotency_key`: replay 時に重複実行を防ぐ key または生成規則
- `target_resolution`: `search-before-create` など、対象を一意に解決する規則

この静的契約は外部書き込みを承認しない。実行時も project policy と user approval が必要である。

### State

- `scope`: `context`、`planning`、`run`、`artifact`
- `writer`: node id または `lead`
- `provenance`: 正本または生成証拠への短い参照

値そのものを contract に詰め込まず、Team Journal、Wayfinder map、workspace artifact、test receipt への参照を流す。

### Edge

- `from` / `to`: node id
- `route`: `static`、`deterministic`、`model`、`human`
- `condition`: 条件付き edge の判定を説明する
- `loop`: 戻り edge の場合だけ `true`

同じ source node の edge は routing owner を混在させない。checkable な条件は `deterministic`、解釈が必要な場合だけ `model`、承認や選好は `human` を使う。

loop edge は必ず正の `max_iterations` と機械的に確認できる `stop_condition` を持つ。agent が tool を呼ばなくなったことは stop condition ではない。

## Validation

```bash
python3 scripts/validate-graph-contract.py \
  templates/graph-engineering/graph-contract.example.json
```

validator は少なくとも次を拒否する。

- 到達不能 node
- 存在しない node / state 参照
- state writer と node write の不一致
- checker / judge による artifact write
- safety contract のない external side effect
- brake のない loop
- 一つの source node における routing owner の混在

## Execution protocol

1. `context/workflow-rules.md` の Phase 0-2.5 を完了する。
2. graph adoption boundary を確認し、contract を task memory に置く。
3. validator が PASS するまで実行を開始しない。
4. edge の前提が満たされた node だけを frontier とする。
5. `context/agent-team-routing.md` の Delegation Gate を通った node だけを sub-agent に委任する。
6. writer は一人に固定し、checker / judge は fresh evidence を読む。
7. node ごとに `templates/graph-engineering/graph-run.md` 形式の receipt を Team Journal または task memory に残す。
8. 不合格時は contract の edge に従い、`max_iterations` を超えたら停止して人間へ escalate する。
9. terminal node、Sprint Contract、Outcome Trace、holistic check がすべて完了した時だけ job 完了とする。

runtime に native graph API がなくても、lead が同じ contract と receipt を使って逐次実行する。capability の有無で安全条件を下げない。

## Debugging order

壊れた作業単位に最も近い layer を直す。

1. 一つの node 内の指示不備なら prompt / context。
2. tool、test、error handling の不備なら harness。
3. completion check、budget、再試行の不備なら loop。
4. node boundary、routing、shared state、authority の不備なら graph。

graph の失敗を prompt の書き直しだけで覆わない。
