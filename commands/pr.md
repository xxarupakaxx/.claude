---
name: pr
allowed-tools: Bash(git:*), Bash(gh:*), Bash(python3:*), Agent, Read, Write
argument-hint: [base-branch]
description: Evidenceに拘束された文案を検証し、承認後にDraft PRを作成
---

# /pr

PR本文の文案生成とGitHubへのexternal writeを分離する。文案workerはtoolなしのproposalだけを返し、leadがEvidence、template、base/head、principal、承認を検証してからDraft PRを作る。

## 境界

- base branchとhead branchを明示し、生成時と作成直前のSHAを拘束する。
- Evidence Bundleが不完全、CRITICAL / IMPORTANTが未解決、未承認writeがある場合は停止する。
- workerへGit/GitHub tool、command、approval、認証済みsessionを渡さない。
- `gh pr create --dry-run`はpushを伴う場合があるためpreflightへ使わない。
- PR作成はverified approval evidenceまたは明示されたproject policyが対象repositoryと操作を許可する場合だけ行う。

## 1. repositoryとPR範囲を確定する

現在branch、remote、head SHAを確認する。base argumentがなければproject `CLAUDE.md`のbase policyを使い、それもなければ候補をread-onlyで調べて一つに確定する。暗黙のfallbackで作成しない。

base/head SHAとchanged pathsを次で固定する。全changed pathを`--allowed-path`へ列挙し、delete/renameは依頼範囲と一致する場合だけ明示許可する。

```bash
python3 ~/.claude/scripts/git_delivery_contract.py range <repo-root> \
  --base <base-sha> --head <head-sha> \
  --allowed-path <path-1> --allowed-path <path-2>
```

`DRAFT_BLOCKED`なら文案作成へ進まない。
既定出力はraw diffを除いた永続snapshotである。本文生成にpatchが必要な場合だけ、同じallowlistとbase/headで`range --include-worker-patch`を再実行し、永続snapshotと`source_hash`が一致することを確認して一時入力として直接渡す。

## 2. Evidenceとtemplateを入力へ束縛する

Evidence Bundleからacceptance evidence、tests、findings、residual risks、writes performedを取得する。repositoryのPR templateを読み、必須headingを`template_sections`へ記録する。

`Delivery Draft Input`にはsnapshotの`source_hash`、base/head SHA、changed paths、Evidence ID、acceptance/test/risk ID、template sections、policy sourceを入れる。raw diffはsnapshotが安全と判定した`worker_patch`だけを一時的に渡し、長期memoryへ保存しない。

## 3. haiku workerは文案だけを返す

要約が必要なPR本文は`rules/model-routing.md`のL1 haikuへ委譲できる。

```bash
python3 ~/.claude/scripts/draft_delivery_message.py prompt <temporary-input.json> \
  --expected-source-hash <trusted-snapshot-hash> --snapshot <range-snapshot.json>
```

`--snapshot`は`changed_paths`をsnapshotと照合する。`PROMPT_READY`の`prompt`をそのまま`Agent(model: "haiku")`へ渡し、JSONだけを返させる。promptにtool使用、判断、副作用の依頼を足さない。返答をtask-localな一時fileへ保存する。`DRAFT_BLOCKED`や起動失敗では別のmodelへfallbackせずleadが本文を書く。

outputはtitle、summary、why、trade_off、out_of_scope、impact、tests、residual_risks、template固有section、`claim_references`を含む。`status`は`DRAFT_READY`または`DRAFT_BLOCKED`だけとする。

## 4. leadが本文を検証する

まず構造を検証する。この段階は`verification: structure_only`であり、PR作成に使えない。

```bash
python3 ~/.claude/scripts/draft_delivery_message.py validate <temporary-input.json> <worker-output.json> \
  --expected-source-hash <trusted-snapshot-hash>
python3 ~/.claude/scripts/draft_delivery_message.py claim-evidence <worker-output.json> \
  --expected-source-hash <trusted-snapshot-hash> > <evidence.json>
```

leadは各test、risk、影響範囲を実差分とEvidenceへ戻って確認し、`checks`へ確認した内容を1行ずつ書いてから`status`を`pass`にする。`checks`が空の`pass`は拒否される。

```bash
python3 ~/.claude/scripts/draft_delivery_message.py validate <temporary-input.json> <worker-output.json> \
  --expected-source-hash <trusted-snapshot-hash> --claim-evidence <evidence.json>
```

`verification: claim_verified`の`draft`だけをtask-localな平文fileへ保存する。意味reviewを飛ばした本文を使わない。既存templateの項目を削除せず、state diagramはcommit済みrepository pathまたは検証済み関係要約だけを使う。

## 5. external write gateを通す

`gh auth status`で現在のGitHub principalを確認し、remote ownerと照合する。別accountへ自動切替しない。verified approval evidenceがrepository、push、Draft PR作成を許可していることを確認する。

作成直前にbase/head refを再解決してdriftを確認する。`--expected-source-hash`はsnapshot fileとは別に保持した値を渡し、`--allowed-path`とdelete/rename policyは最初と同じものをleadが再指定する。

```bash
python3 ~/.claude/scripts/git_delivery_contract.py check-range <repo-root> <range-snapshot.json> \
  --expected-source-hash <trusted-snapshot-hash> \
  --base-ref <base-branch> --head-ref <head-branch> \
  --allowed-path <path-1> --allowed-path <path-2>
```

`DRAFT_STALE`または`DRAFT_BLOCKED`なら本文を使わず、snapshotから作り直す。

## 6. Draft PRを作成する

headが対象remoteへpush済みであることを確認した後、次の形で明示する。

```bash
gh pr create --draft \
  --base <base-branch> \
  --head <head-branch> \
  --title "<validated-title>" \
  --body-file <validated-body-file>
```

作成後にPR URL、number、base/head SHAを取得し、Evidence Bundleの`writes_performed`へ記録する。

## 完了報告

- PR URLとnumber
- base/head branchとSHA
- Evidence Bundle、test、review結果
- verified approval evidenceの参照
- 対象外dirty stateと残存リスク
