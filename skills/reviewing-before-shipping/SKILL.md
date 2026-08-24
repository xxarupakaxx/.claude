---
name: reviewing-before-shipping
description: ブランチやPRをリリース前に点検し、根拠付きでSHIP／DO NOT SHIPを判定する。「出荷前チェックして」「マージしてよい？」「pre-flightレビューして」「リリースのblockerを探して」と依頼されたときに使う。
---

# 出荷前レビュー

安定していた固定点から現在までの変更を調べ、未解決の前提と検証不足を閉じてから出荷可否を判定する。

## 既存設定との関係

- Phase 0〜5.5と必須レビューは`@context/workflow-rules.md`を正本とする。
- Standards／Specの二軸レビューは`reviewing-code`へ委ねる。このSkillでは同じレビューを複製しない。
- `sequential-review-pre-pr`と`auto-reviewing-pre-pr`が必要なprojectでは、その結果を出荷判断の証拠として使う。
- レビュー依頼はread-onlyである。修正、commit、push、PR作成は、ユーザーが別途依頼した場合だけ行う。

## 1. 比較範囲を固定する

ユーザーがcommit、branch、tagなどの固定点を指定した場合は、その値を使う。
指定がなければproject設定のbase branch、`origin/HEAD`、`main`、`master`の順で解決可能なものを選ぶ。

次を確認し、失敗した場合はレビューを始めない。

1. 固定点と`HEAD`がcommitへ解決できる。
2. 固定点と`HEAD`のmerge-baseが存在する。
3. `git diff --find-renames <fixed-point>...HEAD`に変更がある。

比較に使う固定点、merge-base、diff commandを最初に記録し、その後は同じ条件を使う。

`HEAD`に含まれない変更は別枠で確認する。

- staged diff
- unstaged diff
- untracked file

これらをbranch差分へ暗黙に混ぜず、出荷対象に含むかを明示する。

## 2. 変更と周辺契約を調べる

全体diff、変更file一覧、commit一覧を読み、各変更の周辺コードと既存契約を確認する。

該当するものだけを追う。

- public API、schema、data model、migration
- auth、権限、secret、個人情報
- config、feature flag、dependency、build／deploy設定
- error handling、retry、rollback、observability
- test、fixture、manual verification
- documentation、operator手順、互換性

`reviewing-code`が利用可能なら、同じ固定点で実行し、StandardsとSpecのfindingを証拠へ取り込む。
projectの必須checkerがあれば、そのfreshな結果も使う。

## 3. Findingを検証する

推測だけのfindingを出さない。
各findingは次を満たす。

- severity: `BLOCKER`、`IMPORTANT`、`MINOR`
- evidence: file path、line、diffまたは再現結果
- impact: 誰にどの失敗が起きるか
- verification: 実際に確認した方法
- action: 出荷前に必要な最小対応

変更が安全に見えるだけの場合も、確認した契約と検証結果を示す。
別の環境、権限、データがなければ検証できないことは、未確認として残す。

## 4. 暗黙の前提を閉じる

まずcode、test、spec、履歴から答えを探す。
それでも出荷判定を変える未決事項だけをユーザーへ確認する。

- 一度に一問だけ尋ねる。
- 質問ごとに推奨回答と、その根拠を添える。
- 前の回答に依存する問いは、回答後に続ける。
- 好みの確認ではなく、出荷条件に影響する問いへ絞る。

重要な前提が一つでも未解決なら、SHIPを出さない。

## 5. Freshな検証を行う

変更riskに対応する最小の独立checkを選ぶ。
既存のtest、lint、typecheck、build、migration check、task-level workflowを優先する。

実行できなかったcheckは、成功として扱わない。
失敗が変更由来か既存不具合かを分け、根拠がなければ断定しない。

## 6. 出荷可否を判定する

### SHIP

次をすべて満たす場合だけ判定する。

- BLOCKERが0件。
- 重要な前提がすべて解決済み。
- 変更riskに必要なcheckが成功している。
- migration、rollback、運用手順が必要な変更では、その準備を確認済み。
- 残存riskを受け入れられる根拠がある。

### DO NOT SHIP

いずれかを満たす場合に判定する。

- BLOCKERが残っている。
- 重要な前提が未解決。
- 必須checkが失敗、または未実行。
- 互換性、migration、rollback、認可、データ保全の根拠が不足している。

固定点不明、空diff、repository不一致でレビュー自体が成立しない場合は、判定を作らず`REVIEW BLOCKED`とする。

## 出力形式

```markdown
## 出荷前レビュー

- 固定点: <refとcommit>
- merge-base: <commit>
- 対象: <branch差分と未commit差分の扱い>

### Findings
重大度順。0件なら、確認した主要契約を記載する。

### 未解決の前提
なし／確認が必要な事項。

### 検証
実行したcheck、結果、未実行理由。

### 判定
SHIP／DO NOT SHIP／REVIEW BLOCKED

### 出荷前の必須対応
判定を変えるために必要な最小action。なければ「なし」。
```
