---
name: commit
allowed-tools: Bash(git:*), Bash(python3:*), Agent, Read, Write
argument-hint: [--push]
description: 検証済みの変更だけをcommitし、必要時に文案をtoolなしのhaiku workerへ委譲
---

# /commit

commit文案の生成とGit副作用を分離する。文案workerはtoolなしで文案だけを返し、exact staging、事実確認、commit、pushはleadが行う。

## 境界

- 文案の事実源は、Evidence Bundleと`git_delivery_contract.py`が固定したstaged snapshotだけである。
- workerへGit/GitHub tool、command、approval、external writeを渡さない。
- worker出力は未信頼のproposalであり、`validate --claim-evidence`を通るまで使用しない。
- commitはlocal Git write、pushはexternal writeとして別gateにする。
- `git add -A`、暗黙の全stage、here-documentによるmessage展開を使わない。

## 1. 対象を確定してexact stagingする

`git status --short`、対象差分、直近logを確認する。user由来のdirty stateを分け、今回の対象pathだけを明示してstageする。deleteまたはrenameは依頼範囲と一致する場合だけ個別に許可する。

stage後に次を使い、各対象を`--allowed-path`で列挙したsnapshotを作る。

```bash
python3 ~/.claude/scripts/git_delivery_contract.py staged <repo-root> \
  --allowed-path <path-1> --allowed-path <path-2>
```

`DRAFT_BLOCKED`、空差分、対象外path、unmerged、未許可delete/rename、secret、上限超過があれば文案生成へ進まない。secret hitがscanner自身のpatternまたは明示的なfake test fixtureだけだとleadが対象行を直接確認した場合は、hit pathと根拠をEvidenceへ残し、`worker_patch`を渡さずL0 local文案へ戻せる。実credentialの可能性が残る場合やその他のviolationではcommitへ進まない。
この既定出力は`worker_patch`を除いた永続snapshotであり、task memoryへ保存できる。

## 2. Localかhaiku workerかを選ぶ

単一目的で定型的なsubjectだけならlocal templateを使う。複数の意図、理由、trade-offを短く要約する価値が、委譲と統合のコストを上回る場合だけ`rules/model-routing.md`のL1 haikuを使う。

workerへ渡すのは、`Delivery Draft Input`、snapshotのpath/stat/hash、安全な範囲の`worker_patch`、Evidence参照だけである。raw diffが必要な場合だけ同じexact allowlistで`staged --include-worker-patch`を再実行し、永続snapshotと`source_hash`が一致することを確認してmemoryへ保存せず一時入力へ置く。

```bash
python3 ~/.claude/scripts/draft_delivery_message.py prompt <temporary-input.json> \
  --expected-source-hash <trusted-snapshot-hash> --snapshot <staged-snapshot.json>
```

`--snapshot`は`changed_paths`をsnapshotと照合する。`PROMPT_READY`の`prompt`をそのまま`Agent(model: "haiku")`へ渡し、JSONだけを返させる。promptにtool使用、判断、副作用の依頼を足さない。返答のJSONをtask-localな一時fileへ保存する。`DRAFT_BLOCKED`や起動失敗では別のmodelへfallbackせずleadが文案を書く。

commit outputは次を満たす。

- `status`: `DRAFT_READY`または`DRAFT_BLOCKED`
- `content.type`: 許可されたgit-cz type
- `content.subject`: 日本語、70文字以内、絵文字なし
- `content.body`: 必要な場合だけwhat / why / trade-off
- `claim_references`: inputで許可したpath、acceptance、test、riskだけ

## 3. leadが文案を検証する

まず構造を検証する。

```bash
python3 ~/.claude/scripts/draft_delivery_message.py validate <temporary-input.json> <worker-output.json> \
  --expected-source-hash <trusted-snapshot-hash>
```

この段階の結果は`verification: structure_only`であり、commitに使えない。次にcontent hashへ束縛した雛形を得る。

```bash
python3 ~/.claude/scripts/draft_delivery_message.py claim-evidence <worker-output.json> \
  --expected-source-hash <trusted-snapshot-hash> > <evidence.json>
```

leadが実差分を読み、type、subject、bodyの各主張を確認してから、`checks`へ確認した内容（読んだ差分、照合したtest / risk）を1行ずつ書き、`status`を`pass`にする。`checks`が空の`pass`は拒否される。

```bash
python3 ~/.claude/scripts/draft_delivery_message.py validate <temporary-input.json> <worker-output.json> \
  --expected-source-hash <trusted-snapshot-hash> --claim-evidence <evidence.json>
```

`verification: claim_verified`の`draft`だけを、task-localな一時fileへ平文のmessageとして保存する。意味reviewを飛ばした文案を使わない。workerにはfileを書かせない。

## 4. driftを再確認してcommitする

実行直前に、保存したsnapshotへdrift checkを行う。`--expected-source-hash`はsnapshot fileとは別に保持した値を渡し、`--allowed-path`とdelete/rename policyは最初と同じものをleadが再指定する。

```bash
python3 ~/.claude/scripts/git_delivery_contract.py check-staged <repo-root> <staged-snapshot.json> \
  --expected-source-hash <trusted-snapshot-hash> \
  --allowed-path <path-1> --allowed-path <path-2>
```

結果が`DRAFT_STALE`または`DRAFT_BLOCKED`ならcommitせず、snapshotから作り直す。

`READY`の場合だけ次を実行する。

```bash
git commit --file=<validated-message-file>
```

commit後にSHA、実際のchanged paths、hook結果を確認し、Evidence Bundleの`writes_performed`へ接続する。

## 5. pushは別gateで行う

`--push`が指定されても、project policyまたはverified approval evidenceがpush対象を許可していることを確認する。remote、branch、現在のprincipalを確認し、accountを自動切替しない。許可がなければcommit済みで停止し、push待ちとして報告する。

## 完了報告

- commit SHAとmessage
- committed paths
- test / hook結果
- pushの実行有無とremote
- 対象外dirty stateの残存状況
