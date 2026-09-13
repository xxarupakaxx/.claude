---
name: auto-reviewing-pre-pr
description: ユーザーが自動レビュー、独立 reviewer による並列レビュー、または PR 前チェックを明示的に求めたとき、fresh な差分と検証結果をリスクに応じて確認する。通常の自己レビューや PR 作成だけには使わない。
context: current
---

# Pre-PR Auto Review

maker の自己申告だけで完了扱いにせず、独立 checker が fresh な diff と必要な test を直接確認する。finding、検証、残存リスクを Evidence Bundle と `${MEMORY_DIR}/memory/<task>/05_log.md` に記録し、PR作成は最終承認後に限る。

## 適用範囲

`/auto-reviewing-pre-pr`、または「自動レビューして」「独立 reviewer でレビューして」「PR前の自動チェック」と明示された場合に使う。一般的な一人のコードレビューは `pr-review`、意図を詰める対話は `interrogating-pre-pr` に渡す。

## 1. 差分と観点を固定する

```bash
git diff $BASE_BRANCH --stat
git diff $BASE_BRANCH --name-only
```

変更ファイル、実行した検証、関連する契約を読み、`context/workflow-rules.md` の reviewer 選択基準から Done を変え得る最小の観点を選ぶ。認証、認可、個人情報、課金、外部 write、不可逆操作、データ移行があれば `security-reviewer` を必須にする。リスクに無関係な reviewer の固定 fan-out はしない。

独立 reviewer を起動する場合は、利用可能な reviewer/worker 機構を使い、変更対象、完全な diff または参照先、観点、検証結果、未確認点だけを渡す。利用可能な機構がない場合は、無理に名前を仮定せず read-only の代替確認と制約を報告する。

過去の類似 finding はローカルの `solutions/`、`issues/`、`memories/` を検索してから必要な場合だけ reviewer に渡す。見つからなければ検索を続けるために作業を止めない。

API route をレビューするときは diff だけで判断せず、呼び出し先の usecase/repository、関連 domain entity、migration、アプリ側 default を追う。全 path/body/query parameter の認証（誰か）と認可（何にアクセスできるか）を分け、既存行動への遡及影響を確認する。

## 2. ラウンドと収束

### Round 1

選んだ reviewer を独立に実行する。各 finding は `CRITICAL`、`IMPORTANT`、`MINOR`、`info-needed` のいずれかにし、`file:line`、観測事実、影響、具体的な修正案、証拠を付ける。

### Round 2 以降

CRITICAL はすべて修正する。正しさ・安全性・一貫性に関わる IMPORTANT も修正し、修正した path または未解決 finding の観点だけを targeted re-review する。対象が0なら fresh な静的解析と対象 test を実行し、`reviewer rerun: none` と理由を記録する。

通常の収束上限は3ラウンドとする。CRITICAL、判断を要する IMPORTANT、または `info-needed` が残る、同じ finding が3ラウンド続く、あるいは3回連続で LLM だけが修正した場合は、追加の自動修正を続けず人間判断へ移す。MINOR を残す場合は理由と影響を最終報告に書く。

3回連続で LLM だけが修正したときは、次のラウンドで対象 test、lint/typecheck、必要な静的解析を実行し、全選定 reviewer を再起動する。4回以上連続で同じ方法を使わない。

各ラウンドについて、起動・除外した reviewer、finding の新規/重複、修正、検証、残存リスクを `05_log.md` に残す。導入後の運用評価を行う場合だけ、最初の5回について起動数、再起動数、unique finding、escaped defect を集計する。未計測期間を品質向上の証拠にしない。

## 3. Finding の記録

必要な場合、`${MEMORY_DIR}/issues/{priority}-{reviewer}-{title}.md` に次の frontmatter を保存する。既存 field は保持し、issue 本文やログへ secret を書かない。

```yaml
---
priority: CRITICAL       # CRITICAL / IMPORTANT / MINOR
category: sec
type: bug
issue_id: ISS-001
detected_by: security-reviewer
first_detected_round: 1
status: pending          # pending / fixed / reopened / dismissed
re_review_priority: high # high / medium / low
---
```

同じ `issue_id` が pending のままなら検出元 reviewer を優先して再確認する。修正後は `fixed`、該当しなくなった理由がある場合は `dismissed` として記録する。`checkpoint.md` を使う workflow では、issue_id、path、検出元、round、status を各ラウンドに同期する。

## 4. 最終報告と gate

```markdown
## Pre-PR Auto Review 結果
- ラウンド: <実施数 / 上限>
- 初回 finding → 最終残存: <件数>
- reviewer: <選択 / 除外と理由>
- 検証: <実行 command と結果。未実行は理由>
- 残存リスク: <MINOR または未確認>
- 判定: <PR作成可 / 人間判断待ち>
```

CRITICAL、正しさに関わる IMPORTANT、未解消の `info-needed` がある場合は PR 作成を許可しない。全員が PASS でも、通常の diff 確認と test の証拠を省略しない。外部コメント、ラベル、PR作成、公開、commit は、それぞれユーザーの明示した write scope と gate がある場合だけ実行する。
