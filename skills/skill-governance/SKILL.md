---
name: skill-governance
description: Third-party Agent Skill の発見、評判調査、隔離監査、価値評価、採用、更新、廃止候補化を安全に管理する。外部 Skill を入れたい、skills.sh や GitHub の候補を比較したい、既存 Skill の provenance や drift を確認したいときに使う。通常の採用済み Skill の利用先選択には使わない。
disable-model-invocation: true
---

# Skill Governance

候補カタログと runtime の active Skill を分離する。既定動作は read-only であり、第三者コードを審査前に実行しない。

## 起動境界

- 採用、更新、deprecate、retire、delete は user-invoked とする。
- inventory、audit、source drift の確認は `skill-stocktake` から read-only で呼び出してよい。
- 採用済み Skill の routing は `ask-skill-router`、取得 primitive は system `skill-installer`、棚卸し判定は `skill-stocktake` が所有する。
- popularity、publisher 名、scanner pass のどれか一つで trust gate を解除しない。

## 最初に行うこと

1. [references/lifecycle.md](references/lifecycle.md) を読む。
2. [references/baseline-2026-07-15.md](references/baseline-2026-07-15.md) で全surfaceの基準値とarchitecture系の責務を確認する。
3. [references/source-reputation-2026-07-15.md](references/source-reputation-2026-07-15.md) で評判をadvisory evidenceとして確認する。
4. authority と replica が一致するか確認する。

```bash
uv run --offline --python 3.13 --with pyyaml==6.0.2 python -B ~/.codex/skills/skill-governance/scripts/governance.py audit
python3 ~/.codex/skills/skill-governance/scripts/governance.py parity
```

`audit` と `lock-plan` は、upstream receiptのcaptured YAMLを再検証するため、上記のpinned PyYAML環境で実行する。`--offline` cacheがなければprovisioningを別操作として扱い、検査を省略したり暗黙にnetworkへ切り替えたりしない。

`DEGRADED`、registry-lock mismatch、baseline drift があれば、promotion、update、retire、delete、runtime mutationを停止する。`approved`より前、および`rejected`、`retired`、`revoked`のSkillがruntime rootに残っていても停止する。`inventory`、`catalog`、`sources`、`inspect`、`validate-frontmatter`、`lock-plan`、`estate-plan`などのread-only調査は、そのcommand自身にBLOCKING findingがない範囲で続行してよい。

## Lifecycle

### 1. Discover

source の metadata、license、固定 commit、一次情報、評判の反証を集め、`watch` として提案する。star と install 数は discovery signal に限定する。

```bash
python3 ~/.codex/skills/skill-governance/scripts/governance.py sources
python3 ~/.codex/skills/skill-governance/scripts/governance.py reputation
python3 ~/.codex/skills/skill-governance/scripts/governance.py sources --live --source mattpocock-skills
python3 ~/.codex/skills/skill-governance/scripts/governance.py catalog
python3 ~/.codex/skills/skill-governance/scripts/governance.py catalog --live --source mattpocock-skills
```

`--live` は明示的な network-read であり、local file を更新しない。匿名 GitHub API の上限を超える場合は、`GITHUB_TOKEN="$(gh auth token)"` をコマンド環境へだけ渡す。token は registry、lock、receipt、出力へ保存しない。

### 2. Quarantine

候補は runtime root の外へ、`<quarantine>/<source-id>/<40-char-sha>/<upstream-skill-name>` の形で取得する。`main`、`latest`、live symlink を使わない。取得中に candidate の script、hook、package setup を実行しない。quarantineは `SKILL.md` だけでなく、同じupstream directoryの全file、path、実行bitを `package_tree_sha` と一致させる。SOURCE、LICENSE、adaptationを勝手に混ぜず、review stageで明示する。

system installer を fetch primitive として使う場合も、`--ref <full-sha>` と runtime 外の `--dest` を必須にする。取得と採用は別操作である。

### 3. Inspect

```bash
python3 ~/.codex/skills/skill-governance/scripts/governance.py inspect \
  "$HOME/.local/share/skill-governance/quarantine/mattpocock-skills/$FULL_COMMIT_SHA/$SKILL_NAME"
```

frontmatter が strict subset を超える場合は fail-closed になる。full YAML 検証が必要なら、candidate code を実行せず pinned adapter を使う。full adapterもanchor / aliasを受け付けず、depthとevent数を制限する。receipt、lock、catalogなどのJSONは重複keyと非有限数を拒否する。

```bash
uv run --offline --python 3.13 --with pyyaml==6.0.2 \
  python ~/.codex/skills/skill-governance/scripts/governance.py \
  validate-frontmatter \
  "$HOME/.local/share/skill-governance/quarantine/mattpocock-skills/$FULL_COMMIT_SHA/$SKILL_NAME" \
  --target common
```

`--offline` はPyYAML 6.0.2が既にuv cacheにある場合だけ成功する。初回provisioningで `--offline` を外す操作はnetwork-read + cache-writeであり、候補codeの実行とは分けて明示する。

静的 finding が0でも安全証明にはならない。auditはcaptured quarantine treeに対して静的検査を毎回再計算し、そのtree hashがprovenance captureと一致することを確認してから、exact resultをsubjectとsafety receiptへbindする。full YAML receiptが置き換えられるのはstrict parserの明示したYAML構文findingだけである。全 file、命令、依存、外部参照を人間が確認する。

review済みartifactは `<review>/<collection-id>/<local-skill-name>/<target-id>` に置く。quarantine、review stage、runtimeは互いに重ならない。review stageのfull frontmatter receipt、SOURCE、license evidence、adaptation artifactを揃え、`approved` はこのtreeをhash対象にする。runtimeへはまだ置かない。

### 4. Evaluate value

安全性と価値を分ける。代表 prompt で baseline と candidate を比較し、`references/lifecycle.md` の value receipt を作る。`eval-harness` は evidence producer であり、approval の正本ではない。

### 5. Approve and promote

per-skill の catalog path / blob / complete package tree、path/hash-bound adaptation artifact、upstreamとlocalのlicense evidence、quarantine/review manifest、full frontmatter receipt、再計算した静的検査、全target tree hash、安全審査receipt、value receipt、reviewer、人間 approval を揃える。human approvalは同じsubjectとsafety / value receipt本体のhashへbindする。`next_review_date` が現在日より前なら再審査する。promotion receiptはquarantine、approved review tree、runtime反映前後のhashをbindし、前後の `skill-tree-sha256-v1` が一致しなければ停止する。

この Skill は auto-apply を提供しない。target diff を提示し、明示承認後に path 限定で反映し、Codex と Claude を個別 commit する。

### 6. Monitor and retire

update は通知だけ行い、新 artifact として再審査する。retire は registry と routing の状態変更を先に行い、file delete は別承認にする。usage が観測されないことだけを retire 根拠にしない。

## Commands

| Command | Capability | Mutation |
| --- | --- | --- |
| `inventory` | registryで宣言した全scope / root、除外、collisionを列挙 | なし |
| `catalog` | 固定済みsource catalogの内部整合性を確認 | なし |
| `catalog --live` | 固定commitのGit treeと全path / blob SHAを照合 | network-readのみ |
| `reputation` | registryとは独立した日付付き評判snapshotの1対1 coverageとsource bindingを検証 | なし |
| `audit` | registry、lock、baseline、collision を検査 | なし |
| `inspect PATH` | candidate の全 file と危険 signal を検査 | なし |
| `validate-frontmatter PATH` | captured bytesをpinned PyYAML adapterで完全検証 | なし。初回uv provisionだけ別途network / cache mutation |
| `sources` | watch source を表示 | なし |
| `sources --live` | GitHub の current revision を照会 | network-read のみ |
| `parity` | Codex authority と Claude replica を比較 | なし |
| `lock-plan` | proposed lockをstdoutへ表示 | なし |
| `estate-plan` | 全runtime surfaceのexact estate baselineをstdoutへ表示 | なし |
| `delivery --live` | scoped pathのclean HEAD、固定fetch / push URL、origin/mainを照合 | network-read + credential-helper read |

機械可読な結果が必要なら各 command に `--json` を付ける。

## Stop conditions

- immutable commit または content hash を確定できない。
- license、stated purpose、実際の capability が一致しない。
- credential、hook、global config、mutable external instruction を必要とする。
- obfuscation、download-and-execute、symlink、unreviewed binary がある。
- authority / replica が別 generation、または片側だけ push 済みである。

停止時は勝手に例外化せず、evidence と必要な承認を報告する。

## imozuruの固定された制限付き導入

`marycache-imozuru-2026-10` だけは、標準auditと別の `restricted-audit` で検証する。これは固定commitのimozuru、4targetの同一tree、専用runner、統合設定、個別の審査証拠とユーザー承認、両repositoryへの送達に限定する。標準auditのDEGRADED・mutation禁止、標準L2判定、既存4つの管理fileは変更しない。他のSkillや更新へ適用しない。

固定したPython環境で次を実行する。`ready`は反映前後の一致を検査する。`active`は両pushの送達証拠も要求する。いずれもread-onlyであり、自動反映しない。既定の終了値は全体のずれも含む従来の判定を維持する。imozuruの起動では次の限定判定を使う。

```bash
/Users/yoshiki/.local/share/skill-governance/runtime/pyyaml-6.0.2/bin/python -I -B <skill_dir>/scripts/governance.py restricted-audit --phase ready --json
/Users/yoshiki/.local/share/skill-governance/runtime/pyyaml-6.0.2/bin/python -I -B <skill_dir>/scripts/governance.py restricted-audit --phase active --json --require-capability --summary
```

`<skill_dir>`はこのSkillの絶対pathへ置き換える。profileは `restricted-profiles/marycache-imozuru-2026-10/` の4fileで管理する。6種類の検査証拠と送達記録はruntime外の `~/.local/share/skill-governance/` に置き、pathとhashを照合する。公開Webの取得は `imozuru/scripts/run.py` からだけ行い、固定scope `imozuru-public-source-v1`の`capability_status=active`かつ終了値0でなければ停止する。

限定検査では、Codexの既存除外済み一時directoryにある3種類の補助symlinkについて、固定された宛先と属性が一致する場合だけ乱数path成分を正規化する。symlinkの件数、種類、宛先、属性は比較に残す。通常のglobal auditの出力と、他のpath・findingは変更しない。

送達記録は両origin/mainへ到達した観測時点を示す。checkerはofflineであり、現在のremote状態の継続監視ではない。片側の未送達、期限切れ、固定対象や証拠の欠落・改変は能力も停止する。通常のshell、原典script、別のPython環境への切替や、全体baselineの再生成で回避しない。

schema_version=2・generation=2の固定profileは、全体監査とimozuruの収集能力を分けて記録する。正常に観測・検証した全findingと在庫の完全一致差分だけを`global_drift=HOLD`へ残し、`restricted_status=blocked`も維持する。`--require-capability`を明示したときだけ限定能力の成否を終了値に使い、`--summary`は検査を省かず出力を縮約する。

全体の既知の欠落rootは、固定pathのlstatがENOENTと確認できる場合だけ欠落として記録する。読み取り・parse・schema・件数・root集合・TOCTOUの失敗、未知のaudit/inventory codeは能力も停止する。research・router・HTMLの両home計6packageは全treeを固定し、追加fileやsymlink/hardlinkも拒否する。これらの全fileとrunner、governance、承認chainを同じ送達commitへ結ぶ。他のSkillへの許可や全体baselineの更新には使わない。
