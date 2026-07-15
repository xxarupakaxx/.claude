# Skill Governance Lifecycle

## Trust model

Trust anchor は publisher の人気ではなく、固定した file tree と review receipt である。source reputation、star、install、scanner result は advisory evidence に限定する。

変化の速いstar、fork、issue、maintenance signalは `reputation.lock.json` に保存し、registry / catalog / estate lockから分離する。snapshotはsource ID、GitHub identity、固定revisionへbindするが、更新日と数値のrefreshだけでruntime trust lockを再生成しない。

## States

| State | Meaning | Runtime exposure |
| --- | --- | --- |
| `watch` | metadata だけを追跡する候補 | なし |
| `quarantined` | runtime 外へ固定 revision で取得済み | なし |
| `reviewed` | target別のreview stageでfile / instruction / dependency review 済み | なし |
| `approved` | review stageのexact treeにsafety、value、人間 approval receipt が揃う | まだなし |
| `active` | approved tree と同じ hash で runtime へ反映済み | あり |
| `legacy-active` | 導入済みだが新 governance の receipt が不足 | あり。新規採用の根拠にしない |
| `update-available` | upstream drift を検出。現行approval lineageを維持 | 現行snapshotのみ |
| `rejected` | blocker または value 不足 | なし |
| `deprecated` | route から段階的に外す。現行approval lineageを維持 | 原則、明示起動のみ |
| `retired` | runtime search path から外した | なし。file deleteとは別 |
| `revoked` | security / rights 理由で即時停止 | なし |

正規遷移は `watch -> quarantined -> reviewed -> approved -> active` とする。update は `active -> update-available -> quarantined` に戻して再審査する。

`active`、`update-available`、`deprecated`だけがapproval済みruntime状態である。その他のstateがtarget runtime内に残ればBLOCKINGとする。

## Risk tiers

| Tier | Capability | Default decision |
| --- | --- | --- |
| L0 | 文書のみ、外部参照なし、read-only guidance | full review 後に採用検討 |
| L1 | local script、限定 file write、固定 dependency | 独立 review と都度承認 |
| L2 | network、credential、hook、global config、memory mutation | NO-GO。sandbox は別設計 |
| L3 | destructive command、外部公開、権限委譲、secret操作 | NO-GO。専用の脅威モデルと人間の個別承認が必要 |

## Blocking findings

- immutable commit、tree hash、license evidence の不足。
- stated purpose と command / file / network capability の不一致。
- symlink、submodule、nested archive、unreviewed binary、特殊 file。
- obfuscation、encoded payload、download-and-execute、credential access。
- unpinned dependency、mutable external instruction、package lifecycle hook。
- user approval の迂回、log 抑止、global instruction / memory の変更。
- active root 内で precedence が同じ、または precedence が不明な同名異内容 collision。project root など一意の precedence で解決される shadow は全件 inventory し、advisory として可視化する。
- registry-lock binding、authority-replica generation、baseline hash の不一致。

## Advisory evidence

- publisher、verified badge、star、fork、install count。
- recent activity、release、security policy、OpenSSF Scorecard。
- scanner pass / warning。pass は安全証明ではない。
- usage event。未観測と観測不能を分ける。

## Review receipt

receiptはpackage配下の `receipts/*.json` に置き、registryでは `{ path, sha256 }` で参照する。absolute path、`..`、symlink、hash不一致はBLOCKINGである。

review対象を次の値からcanonical JSON化し、`subject_sha256` を作る。

- collection IDとsource ID。
- skillごとのfull revision。
- adaptation、risk tier、license。
- target rootとcaptured tree hash。
- approved / active ではcatalogのsource identity、revision、root tree SHA、各 `SKILL.md` path / blob SHA、complete package tree SHA、baseline date、path/hash-bound adaptation artifact。
- quarantineとreview targetのexact manifest、license evidence、再計算したstatic inspection、surface-bound full YAML receipt。

安全審査receiptとvalue receiptは同じ `subject_sha256` にbindする。安全審査receiptはupstream binding、quarantine / target manifest、license evidence、capability、dependency、external URL、machine-recomputed static inspection、path/hash-bound local adaptation、reviewer、review date、next review dateを持つ。`next_review_date` がaudit日のUTC dateより前ならBLOCKINGである。approval receiptは安全審査receiptとvalue receiptの両方のSHA-256へbindする。`active` へ進む場合は、同じsubjectとapproval receipt、quarantine hash、approved review hash、runtime反映前後hashへbindしたpromotion receiptを追加する。

safety review evidenceは source、full commit SHA、tree hash、file manifest、license、capability、finding、dependency、external URL、local adaptation diff、reviewer、decision、review date、next review date を持つ。任意の非空文字列やscanner passをapproval receiptとして扱わない。

## Value receipt

安全でも成果が改善しなければ採用しない。次を必須にする。

- representative prompts と選定理由。
- baseline と candidate の識別子。
- runtime、model、trial count、実行条件。
- pass@1 の実測成功率。
- trigger precision、trigger recall、誤起動 / 未起動例。
- outcome rubric と case ごとの結果。
- workflow friction、重複、context cost。
- reviewer、評価日、限界、採用判断。

machine receiptでは `representative_prompts`、`baseline`、`candidate`、`trial_count`、`pass_at_1`、`trigger_precision`、`trigger_recall`、`outcome_rubric`、`reviewer`、`date`、`decision: pass` を必須にする。

`eval-harness` は試行を作る道具であり、この schema と判定を置き換えない。

## Authority and recovery

- parent conflict 解消まで Codex repo が authoritative writer、Claude repo が replica である。
- shared artifact は同じ integer `generation` と `registry_sha256` を持つ。
- 両 repo の local commit を先に作り、Codex、Claude の順に push する。
- 片側 push 失敗は `DEGRADED`。新しい promotion / update / retire を止め、同じ generation の commit を retry する。
- 成功側を自動 revert しない。registry / lock 不一致時はruntime mutationを止める。read-onlyのcatalog、source、inventory、inspect、validate、planは各command自身のBLOCKING findingがない範囲で続け、修復evidenceを作れるようにする。
- parityはgovernance packageの全file set、全byte、executable bitを比較し、`SKILL.md`だけを明示したplatform adapterとして正規化する。integration contractはmarkerだけでなく登録済みblock digestへbindする。
- runtime estateでは `skill-governance` 自身の `estate.lock.json` と `reputation.lock.json` だけ、content hashを固定markerへ正規化する。これは台帳が自分自身をhashする循環と、advisoryな評判更新による無関係なestate churnを避けるための明示的な例外である。両fileの存在、path、modeはestateで、実byteはGit parity、lock validation、deliveryで引き続き検証する。ほかのpackage fileは全内容をhashする。
- quarantine、review、receiptはcanonical pathの全ancestorをFD保持して再検証する。YAML anchor / aliasとbudget超過、JSON duplicate keyを拒否する。
- `delivery --live` はparityとgeneration / registry-lock bindingを再検証し、両repoのgoverned pathがcleanなHEADにあり、`origin`の固定fetch / push URLとその`main`がlocal HEADに一致することを証明する。
- Vaultのunmerged gitlinkはmachine-checkable HOLDとする。HOLDが適用されるrootへのpromotion、update、retire、mirror applyは停止する。

## Promotion checklist

- [ ] quarantine path は runtime search path 外。
- [ ] quarantine path は `<source-id>/<full-sha>/<skill-name>` で、全componentがnon-symlink directory。
- [ ] quarantine全体のGit tree SHAがcatalogのcomplete package tree SHAと一致し、local injectionがない。
- [ ] source は full commit SHA に解決済み。
- [ ] 全 file inventory と canonical hash がある。
- [ ] strict / full frontmatter validation が完了。
- [ ] review stageは `<collection-id>/<skill-name>/<target-id>` にあり、runtime外でSOURCEとlicense evidenceを持つ。
- [ ] safety receipt と value receipt があり、catalog path / blob / tree、target hash、adaptation diffをbindしている。
- [ ] human approvalが同じsubjectとsafety / value receipt本体のhashへbindしている。
- [ ] target collision と platform adapter を確認した。
- [ ] user が target diff と外部状態変更を承認した。
- [ ] promotion 前後 hash が一致する。
- [ ] safety reviewの期限が切れていない。
- [ ] Codex / Claude の test、parity、rollback を確認した。
