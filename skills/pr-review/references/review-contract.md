# PR review contract

`SKILL.md`の全手順で使う詳細契約。PRごとにこのファイルを全文適用する。

## Snapshot acquisition

GitHub APIまたは`gh`から、次を一度に記録する。

```text
repository, pr_number, url, title, body
base_repository, base_ref, base_sha
head_repository, head_ref, head_sha
draft, mergeable, mergeable_state, author
review_started_at
```

現在のprincipalは`gh auth status`等のread-only手段で確認する。認証失敗、repository不一致、権限不足は`BLOCKED`で止める。別accountへの切替はユーザーが選ぶ操作である。

commit objectをlocalに持たない場合は、checkoutせずPR refまたはSHAをfetchする。固定点を得たら次の形で差分を作る。

```bash
git merge-base <base_sha> <head_sha>
git diff --find-renames --find-copies <merge_base_sha> <head_sha>
git diff --name-status <merge_base_sha> <head_sha>
git log --oneline <merge_base_sha>..<head_sha>
```

GitHubのPR pageと通常のcompare pageはmerge baseが異なる場合がある。PR metadata、GitHubのFiles changed inventory、local diffのpath数を突合する。GitHub側の既知の上限で説明できる不足は上限と欠落範囲を記録し、固定SHAのlocal object graphをcoverageの正本にする。説明できない不一致は、差を解決するまで`BLOCKED`とする。

GitHubのList pull request files APIは最大3,000 filesである。GitHubのdiff表示にもPR全体・file・renderable fileの上限がある。上限到達、patch欠落、binary、巨大fileではAPI/UIを完全なcoverage証拠にせず、local object graph、producer固有の検証、PR分割判断を併用する。

snapshotを保存した後はbranch名からdiffを再生成しない。報告前にremoteのbase/head SHAを再取得してmerge-baseを再計算し、driftを判定する。

## Coverage ledger

| class | 確認方法 | gapになる条件 |
|---|---|---|
| `human-authored` | 全diff行と必要なfull-file/contextを読む | 未読行、理解できない挙動、必要なcaller未確認 |
| `test` | testの妥当性、failure感度、production requirementとの対応を見る | production changeに対応するtestがない、testが壊れてもPASSする |
| `docs/config` | runtime・利用者挙動との整合を確認する | codeと設定・docsの意味がずれる |
| `generated/vendor` | generator/source/version/hashと再生成結果を確認する | source不明、手編集、再生成不能 |
| `lock/data` | producer、semantic diff、size、format checkを確認する | 差分を意味として説明できない |
| `binary/submodule` | provenance、hash/pointer、対応source、scan結果を確認する | 内容または由来を検証できない |

各entryは`path`、`class`、`reviewed_by`、`method`、`status: covered|gap`、`note`を持つ。ledgerのpath集合はchanged path集合と完全一致させる。

大規模PRは行数だけで自動rejectしない。ただし、human-authored codeを全行理解できない、必要な専門性を割り当てられない、または独立した変更が混在する場合は`BLOCKED`とし、自己完結したPRへの分割を提案する。

## Context package

reviewerへ渡す最小package:

- 固定したbase/head/merge-base SHAとdiff path。
- 担当するchanged pathとcoverage class。
- 適用される`CLAUDE.md`、style/rule、関連specのpath。
- hunk周辺のfull-file、caller/callee、data flow、guarding test。
- 担当risk、出力schema、read-only境界。

diffだけで認可、データ整合、例外処理を断定しない。変更行から実行経路を追い、guardが別層にある可能性を反証として確認する。

## Risk triggers

`@context/workflow-rules.md`のreviewer選択ガイドを正本とする。次はPRレビュー時の信号であり、reviewer一覧の第二の正本ではない。

| diff signal | 必ず深掘りするrisk |
|---|---|
| auth、permission、resource ID、session、token | security、parameter-level authorization、privacy |
| PII、retention、export、consent、audit log | privacy、compliance、data minimization |
| delete、purge、overwrite、one-way migration | authorization、irreversibility、backup/rollback |
| schema、migration、serialization、default値 | backward compatibility、existing data、rollback |
| public API、event、CLI、config contract | consumer compatibility、error contract、versioning |
| async、queue、transaction、cache、retry | ordering、race、idempotency、partial failure |
| external API、filesystem、notification、billing | failure handling、duplicate side effects、auditability |
| UI、keyboard、focus、form、locale | accessibility、interaction state、i18n |
| CI、IaC、container、dependency | supply chain、secret、deploy/rollback |
| algorithm、query、loop、render path | scale assumption、complexity、N+1、memory |

spec complianceとrepository standards/correctnessはbaselineであり、specialistの有無にかかわらず確認する。

## Finding gate

findingは次をすべて満たす。

```yaml
id: PRF-001
severity: CRITICAL | IMPORTANT | MINOR
title: 短い問題名
location: path/to/file.ext:L42
introduced_by: head SHAまたはhunk
claim: 差分が導入する問題
failure_scenario:
  preconditions: 入力・状態・呼出経路
  behavior: 実際に起きる誤動作
  impact: 利用者・data・security・operationへの影響
evidence:
  changed: path:line と該当する変更
  context: caller、guard、test、spec、ruleのpath:line
counter_evidence_checked: 確認したguard/test/別経路
recommendation: 最小の修正方向
verification: 修正後に証明するtestまたは手順
detected_by: reviewer名
```

### Severity

- `CRITICAL`: exploit、data loss、重大な本番障害、不可逆な破壊、要求の中核を成立させない問題。merge blocker。
- `IMPORTANT`: 再現可能なcorrectness、compatibility、reliability、maintainability違反。merge前に解消する。
- `MINOR`: code healthを改善する任意の提案。個人的好みは含めず、純粋な教育的指摘は`Nit:`と明示する。

severityは問題の種類ではなく具体的impactで決める。「test不足」だけでCRITICALにせず、未検証のfailureと影響を示す。

### Candidate disposition

| 状態 | 扱い |
|---|---|
| schemaを全て満たす | finding |
| failureの可能性はあるがcontext不足 | question |
| 環境・権限・sizeにより検証不能 | residual risk / coverage gap |
| baseにも存在し差分が悪化させない | pre-existing、PR findingから除外 |
| formatter/linterが確実に検出し既存checkが実行される | tooling resultへ委ねる |
| 同じroot causeの別症状 | 一つのfindingへ統合しaffected locationsを列挙 |
| 反証で成立しない | rejected candidate、報告しない |

reviewer間でseverityが違う場合は高い方を機械採用せず、failure scenarioとimpactを再確認して一つに決める。

## Checks

次を別々に記録する。

- `fresh`: このsnapshotに対して実行し、command、exit code、要点を記録したcheck。
- `remote`: 同じhead SHAに紐づくGitHub CI/check。
- `not_run`: 理由付きで実行しなかったcheck。
- `environment_failure`: repository defectと因果を確認できない失敗。

未信頼forkのcheckoutやtest実行は任意コード実行になり得る。明示承認された隔離環境がない限り、remote CIと静的なrepository evidenceを使い、local executionは`not_run`へ残す。

## Merge decision

| decision | 条件 |
|---|---|
| `READY` | snapshot不変、CRITICAL=0、IMPORTANT=0、coverage gap=0、required checksがPASS、merge blockerがない。MINORは残せる |
| `NOT_READY` | CRITICAL/IMPORTANTがある、または差分起因のrequired check failureがある |
| `BLOCKED` | snapshot、spec/permission、coverage、専門性、required checkの証拠が不足し、安全な判断ができない |
| `STALE` | 報告前にbase/head/merge-base SHAが変わった。ほかの判定を無効化し、新snapshotで再reviewする |

draft、GitHub merge conflict、branch protection未充足はreview findingと混ぜず、merge blockerとしてreportする。merge blockerが一つでもあれば`READY`を返さない。

## Report template

```markdown
## Findings

### [IMPORTANT] short title
- Location: `path/file:42`
- Failure: precondition → wrong behavior → impact
- Evidence: changed line + context line
- Recommendation: minimum direction
- Verification: test or observation

### [MINOR][Nit] optional mentoring point
- Reason: code health上の利点と、今回のmergeをblockしないこと

## Questions / residual risks
- ...

## Coverage
- Covered: N/N paths
- Gaps: ...
- Reviewers: selected/skipped with reasons

## Checks
- Fresh: ...
- Remote: ...
- Not run / environment failures: ...

## Merge blockers
- Draft / conflict / branch protection / required review: ...

## Good things
- ...

## Snapshot
- PR: URL
- Base: sha
- Base current: sha
- Head reviewed: sha
- Head current: sha
- Merge base reviewed/current: sha / sha
- Decision: READY | NOT_READY | BLOCKED | STALE
```

## Primary sources

- GitHub Docs, [Pull requests](https://docs.github.com/en/pull-requests/reference/pull-requests): PRのFiles changed、Checks、merge status、PR refs、およびcompare pageとのdiff差異。
- GitHub Docs, [REST API endpoints for pull requests](https://docs.github.com/en/rest/pulls/pulls): PR metadataとList pull requests files（最大3,000 files）。
- GitHub Docs, [Repository limits](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits): PR diff、単一file、renderable fileの表示上限。
- Google Engineering Practices, [What to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html): every line、context、tests、専門reviewer、generated dataの扱い。
- Google Engineering Practices, [How to write code review comments](https://google.github.io/eng-practices/review/reviewer/comments.html): reasoning、guidance、severity label、Nit/Optional/FYI。
- Google Engineering Practices, [The standard of code review](https://google.github.io/eng-practices/review/reviewer/standard.html): code healthを改善すれば完璧でなくてもapproveできる基準。
- Google Engineering Practices, [Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html): self-contained change、tests同梱、大規模changeのreview risk。
- OWASP, [Code Review Guide](https://owasp.org/www-project-code-review-guide/): scannerに加えてmanual security reviewを行う根拠。
- NIST, [SP 800-218 Secure Software Development Framework](https://csrc.nist.gov/pubs/sp/800/218/final): PW.7のreview/analysis、findingとremediationの記録・triage。
- Borg et al., [Rethinking Code Review Workflows with LLM Assistance](https://arxiv.org/abs/2505.16339): LLM reviewにおけるcontext不足、false positive、trust課題とcontext retrievalの必要性。
