# User scope Skill昇格計画

## 目的

Matt Pocock由来のSkillを、CodexとClaudeのuser scopeで利用できる状態へ移す。

ただし、全41件を一括でactiveにしない。

固定revisionで監査済みの分類を使い、価値、誤起動、外部副作用、context負荷を確認できた単位だけを段階的に昇格する。

## 正本と配置

- Codex authority：`~/.codex/context/matt-skill-user-scope-promotion-plan.md`
- Claude replica：`~/.claude/context/matt-skill-user-scope-promotion-plan.md`
- Vault：計画の正本や実行成果物を置かない。

Codex側をauthoritative writerとし、Claude側は同じ意味を持つpaired surfaceとして更新する。

## 現在のuser scope

| Surface | 実体 | 現在HEAD | 同期先 | 状態 |
| --- | --- | --- | --- | --- |
| Codex | `~/.codex`から`/Users/yoshiki/ghq/github.com/xxarupakaxx/.codex`へのsymlink | `f786eff` | 実行時の`origin/main` | fast-forwardが必要。untracked 5件あり |
| Claude | `~/.claude`のGit repository | `1d374c0` | 実行時の`origin/main` | fast-forwardが必要。clean |

調査時点では、Codexのuntracked 5件とincoming tracked pathに衝突はなかった。

Claudeにもlocal未追跡fileとの衝突はなかった。

計画文書自身もuser-scope repositoryへcommitされるため、固定したtarget SHAを本文に自己参照させない。

Wave 0ではfetch後の`origin/main`をtargetとし、incoming pathを再計算する。

現在のuser-scope auditは旧governance codeで実行されるため、BLOCKING 26件を返す。

内訳はactive collision 14件とestate 12件であり、今回の2 commitにselector、estate、symlink防御の修正が含まれている。

## 採用の単位

新しいSkill fileを41件追加する計画ではない。

監査済み41件のうち39件にはすでにlocal対応がある。

未導入だった`batch-grill-me`と`to-questionnaire`は、2026-07-19の再審査で明示起動専用、in-progress表示、外部送信なしを条件に採用へ変更した。

作業の単位は、file installationではなく次の四つになる。

1. user-scope repositoryを監査済みHEADへ同期する。
2. 既存Skillをcohort単位で評価し、legacy-activeからevidence-backed activeへ移す。
3. niche Skillをuser-invokedまたはproject-localへ下げる。
4. deprecated Skillをrouting、selector、runtimeの順にretireする。

## Wave 0：user scopeを監査済みHEADへ同期する

### 対象

- Codex：`f786eff -> 実行時のorigin/main`
- Claude：`1d374c0 -> 実行時のorigin/main`

### 手順

1. 現在HEAD、branch、remote、dirty stateを記録する。
2. `config.toml`、Claude settings、runtime-only fileを内容を表示せずbackupする。
3. incoming tracked pathとuntracked pathの非衝突を再確認する。
4. CodexとClaudeを`git pull --ff-only origin main`で更新する。
5. exact HEAD、user-only fileの保持、selector設定を確認する。
6. governance unit test、audit、parity、catalog、deliveryを実行する。
7. Codex DesktopとClaudeの新規sessionでSkill discoveryを確認する。

### 合格条件

- CodexとClaudeのHEADが、それぞれの`origin/main`と一致する。
- runtime-only fileと秘密設定が失われていない。
- governance auditが`status=ok`、BLOCKING 0になる。
- parityとdeliveryがPASSする。
- 同一Skillが複数の同順位active routeとして表示されない。

### 停止条件

- fast-forwardできない。
- incoming tracked pathとruntime-only fileが衝突する。
- selector反映後もcollisionが残る。
- 片側だけ更新され、parityが崩れる。

## Wave 1：engineering coreを正式昇格する

一括承認を避けるため、関連するSkillを四つのcohortへ分ける。

| Cohort | Skill | 代表成果 |
| --- | --- | --- |
| Route to execution | `mapping-large-projects`、`writing-specifications`、`creating-tracer-tickets`、`implementing-work` | 不明瞭な大型案件から検証可能な実装単位まで接続する |
| Feedback loop | `tdd`、`diagnosing-bugs`、`reviewing-code` | red state、原因、review findingを証拠で閉じる |
| Model and design | `grilling-with-docs`、`modeling-domains`、`designing-codebases` | 未決事項、用語、module境界を分離する |
| Routing and context | `ask-skill-router`、`grilling`、`handing-off-context` | 過剰なSkill起動を避け、fresh contextへ必要情報だけ渡す |

各cohortで次を実行する。

1. fixed revision、complete package tree、license、SOURCEを確認する。
2. local adaptation diffとrisk tierを固定する。
3. representative promptを最低3種類用意する。
4. baselineとcandidateでtrigger precision、trigger recall、pass@1、context負荷を比較する。
5. safety receiptとvalue receiptを同じsubjectへbindする。
6. user approval後にactiveへ昇格する。
7. cohort単位でcommit、test、audit、parity、deliveryを行う。

一つのcohortが失敗しても、ほかのcohortを巻き戻さない。

## Wave 2：限定用途をuser-invokedで採用する

| Lane | Skill | 起動条件 |
| --- | --- | --- |
| Architecture survey | `improving-codebase-architecture`、`brainstorming`、`designing-codebases` | 指定scopeまたは直近hotspotのread-only調査 |
| Prototype | `prototyping-solutions` | 文書だけでは決められない設計判断がある |
| Repository setup | `setting-up-engineering-skills` | trackerやdomain docsが明示的に必要 |
| Education | `teaching-concepts` | 実装が安定し、教育workspaceを作る依頼がある |
| Writing | `writing-fragments`、`writing-shape`、`writing-beats`、`editing-articles` | 執筆タスクとして明示される |
| Vault | `managing-obsidian-vaults` | Vault作業でAGENTSを補助する |
| Workflow | `designing-workflows` | scheduled workflowの設計依頼がある |

これらはglobal defaultにしない。

trigger条件を満たさない場合、`ask-skill-router`は候補として返さない。

## Wave 3：niche Skillをproject-localへ寄せる

次のSkillはuser scopeに存在しても、自動起動の対象にしない。

- `setting-up-ts-deep-modules`
- `migrating-to-shoehorn`
- `scaffolding-exercises`
- `setting-up-pre-commit-hooks`
- `generating-setup-wizards`
- `guarding-git-commands-in-claude-code`

対象repository、package manager、外部副作用が確定した場合だけproject-localで有効化する。

package install、hook、secret、global configを伴う場合は、Skill approvalとは別の実行承認を取る。

## Wave 4：deprecatedと置換対象をruntimeから外す

| Upstream | Local | 処理 |
| --- | --- | --- |
| `design-an-interface` | `design-an-interface` | 旧sub-agent API前提の同名Skillを削除し、`brainstorming`と`designing-codebases`へ分離 |
| `qa` | `conducting-quality-assurance` | `triaging-issues`と`diagnosing-bugs`へ寄せてretire |
| `ubiquitous-language` | `ubiquitous-language` | `modeling-domains`へ寄せてretire |
| `claude-handoff` | `handing-off-to-claude` | shared routeから外し、必要ならClaude専用referenceへ移す |
| `request-refactor-plan` | `planning-refactors` | architecture survey、spec、ticketsの組み合わせへ置換 |

`design-an-interface`、`conducting-quality-assurance`、`planning-refactors`、`ubiquitous-language` は置換参照を更新した後にruntimeから削除する。

`handing-off-to-claude` はdeprecatedではないため、今回の削除対象には含めない。

## Wave 5：継続監視

- upstream更新は`update-available`として通知し、自動更新しない。
- fixed revisionが変わるたびにcatalog live verificationを行う。
- 誤起動、未起動、context負荷をcohort別に記録する。
- 価値が下がったSkillはdeprecatedを経てretireする。
- `batch-grill-me`と`to-questionnaire`はin-progress cohortとして分離し、明示起動、誤起動、回答負荷、local-only出力を継続監視する。

## 完了条件

- user scopeのCodexとClaudeが同じgovernance generationを使う。
- canonical routeが一意である。
- active Skillには期限内のsafety receipt、value receipt、人間approvalがある。
- optionalとniche Skillがmodel-invokedとして誤起動しない。
- deprecated対象がshared routeとruntime searchから外れている。
- audit、parity、delivery、対象testが各waveでPASSする。

## 次の実行単位

2026-07-19の実行単位はWave 0、正式名entry、in-progress 2件、deprecated削除、ロードマップ改善を一つのSprint Contractで追跡する。

現在状態の正本はgovernance catalog、registry、runtime routingとする。

41件の採否判断と置換理由は`context/matt-skill-adoption-map.md`で確認する。

検証は`scripts/validate-matt-skill-integration.py`で行い、完了済み実行の詳細証拠はGit履歴を参照する。
