---
name: skill-stocktake
description: "設定済みの全 Skill root と固定 revision の外部 catalog を棚卸しし、keep / improve / retire / merge を提案する。provenance、collision、利用証拠、runtime 露出を区別し、変更は人間承認後に skill-governance へ渡す。"
---

# Skill Stocktake

## 目的

`skill-governance` の機械 inventory を土台に、Skill estate 全体の品質と役割分担を見直す。単一の `skills/` directory、人気順、観測できた利用回数だけで判定しない。

判定は提案であり、runtime の変更ではない。

- **KEEP**: 現状維持。
- **IMPROVE**: 内容、provenance、adapter、routing、eval の補完候補。
- **RETIRE**: route から外す候補。file 削除とは分ける。
- **MERGE**: 重複責務の統合候補。

## トリガー

- 「スキルを棚卸しして」
- 「使っていないスキルはある？」
- `/skill-stocktake`
- 月1回の read-only maintenance

## 原則

1. configured root を全件列挙し、存在しない root も coverage gap として残す。
2. candidate catalog と active runtime を混同しない。
3. `legacy-active`、`deprecated`、`in-progress`、fixture、mirror、plugin namespace を区別する。
4. 利用履歴がないことと、利用を観測できないことを区別する。0回だけで RETIRE にしない。
5. 同名でも内容が異なる collision と、別名でも同じ出典・責務を持つ alias を調べる。
6. KEEP / IMPROVE / RETIRE / MERGE は証拠付きの提案に限定する。変更、移動、削除、promotion は人間承認後に `skill-governance` へ渡す。

## Step 1: 機械 inventory

authority である Codex package を read-only で実行する。

```bash
python3 ~/.codex/skills/skill-governance/scripts/governance.py inventory --json
python3 ~/.codex/skills/skill-governance/scripts/governance.py catalog --json
python3 ~/.codex/skills/skill-governance/scripts/governance.py audit --json
python3 ~/.codex/skills/skill-governance/scripts/governance.py parity --json
python3 ~/.codex/skills/skill-governance/scripts/governance.py sources --json
```

次を確認する。

- root 別の検出数、missing / skipped path、coverage completeness。
- logical name と raw name の collision。
- registry、lock、catalog、authority / replica generation の一致。
- source revision、全 `SKILL.md` path、fixture / deprecated 等の role。
- license、provenance、review receipt、value receipt の gap。

## Step 2: 利用と参照の証拠

利用履歴は補助証拠として扱う。記録 file が存在しない、runtime ごとに収集範囲が違う、plugin invocation が Skill 名として残らない場合は `unobservable` と記録する。

次も横断確認する。

- global / project instructions、routing table、workflow、schedule、playbook からの参照。
- Codex / Claude の `commands/`、`skills/`、`prompts/`、plugin cache、marketplace、project root。
- 同じ機能が別 artifact 種別または別名で提供されていないか。

schedule、playbook、note から durable に参照されているものは、短期の利用観測が乏しいだけで RETIRE にしない。

## Step 3: cohort review

全件をまず機械分類し、次の cohort を優先して内容を読む。

1. active collision または trigger overlap。
2. `legacy-active`、provenance / license / receipt 不足。
3. upstream drift、deprecated、in-progress。
4. 高権限 script、network、credential、hook、global config を含むもの。
5. 利用価値または routing が不明な長期未観測 Skill。

sub-agent は Delegation Gate を満たす独立 cohort がある場合だけ使う。固定数の agent を無条件に起動しない。

## Step 4: 判定

各判定には次を付ける。

- logical name、全 evidence path、runtime exposure。
- source と固定 revision。分からなければ `unknown`。
- usage evidence の観測範囲と限界。
- overlap / collision / alias の相手。
- safety、value、maintenance cost。
- 提案、owner、再評価日、実行時の approval gate。

`eval-harness` の pass@k は value evidence の一部であり、採用判定そのものではない。

## Step 5: レポートと承認

```markdown
# Skill Stocktake Report — YYYY-MM-DD

## Coverage
- Configured roots: N / N scanned
- Local entries: N
- Pinned source paths: N
- Gaps: N

## Decisions
| Skill / route | State | Proposal | Evidence | Approval needed |
|---|---|---|---|---|
| ... | ... | KEEP / IMPROVE / RETIRE / MERGE | ... | ... |

## Blockers
- active collision
- unpinned source
- unknown license
- authority / replica drift
```

変更へ進む場合だけ、対象 diff、rollback、registry generation を示して承認を取る。承認なしで file の変更、削除、promotion、update、retire を行わない。

レポートは `${MEMORY_DIR}/memory/` 配下へ保存する。
