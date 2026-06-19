---
allowed-tools: Bash(git:*), Bash(gh:*), Read, Write, Workflow, Agent, Skill
argument-hint: [PR番号]
description: PRのCIステータスとレビューコメントを監視し未対応を自動対応する。起動時に /loop で30分おき継続監視を自動開始（Esc で停止）
---

# /pr-watch — PR継続監視・自動対応（CI + レビュー）

PR 1本のCIステータスとレビューコメントを点検し、未対応があれば自動対応する。
**初回起動時に `/loop 30m /pr-watch <PR>` を自動開始**し、以降は30分おきに継続監視する（`Esc` で停止）。

> 内部で `Skill({ skill: "loop", args: "30m /pr-watch [PR番号]" })` を呼び出してループを起動する。2回目以降の呼び出し（ループ再実行時）はスキップして1サイクルのみ実行する。

## 使い方

```
/pr-watch [PR番号]    # 起動 → 自動でループ開始（30分おき継続監視）
```

## 自律方針（CLAUDE.md準拠）

- **自分がauthorのPR**: CI失敗の修正もレビュー指摘対応も自動で commit/push（フル自律）
- **reviewer立場（author≠自分）／author判定が確定できない**: **push 禁止（fail-closed）**。レビューのみ（`autoFix:false`）
- **ESCALATE**: pr-review-loop が3ラウンドで未解決、または同一CI失敗を2回修正しても直らない場合は自動修正を停止し、未解決内容を報告（Slack通知先が設定済みなら通知）
- `git push --force` / `--force-with-lease` は**使わない**。外部書き込みは冪等に（同一CI失敗の二重修正・同一コメントへの二重対応を防ぐ）
- **不確実な状況では常に「対応しない／push しない」側に倒す（fail-closed）**

## フロー（1サイクル）

### 0. state読み込み・対象PR確定・author判定・実行ロック

1. **state読み込み**: `.local/pr-watch-state.json` を Read
   - **未存在 → `{}` として扱う**（`.local/` が無ければ作成）。Read 時の `last_run` を覚えておく（後述の競合検出用）
   - **JSON parse 不能など破損 → fail-closed**: 当該サイクルは自動修正/pushをせず、点検結果の報告のみ行い終了（state を上書きしない）
2. **PR番号を1箇所で確定**し、以降の全 `gh` 呼び出しでこの番号（`$PR`）を使う（各コマンドに `$ARGUMENTS` を裸展開しない）:
   - `$ARGUMENTS` が PR番号（数値）/ PR URL ならそれ。複数トークンなら**先頭のみ**採用
   - 空なら現ブランチのPRを解決: `gh pr view --json number -q .number`
   - 解決できない → 「監視対象のPRなし」と報告して**終了**
3. **PRメタ取得**: `gh pr view "$PR" --json number,title,author,headRefName,state,isDraft,url`
   - **state が OPEN 以外（CLOSED / MERGED）** → state から当該PRキーを**削除して Write** し**終了**（dead branch への push 防止 + state 肥大防止）
3.5. **ループ自動起動チェック（初回のみ）**:
   - state[PR].loop_active が `true` → スキップ（既にループ動作中）
   - state[PR].loop_active が未設定 / false → 以下を実行:
     1. `state[PR].loop_active = true` を state に Write
     2. `Skill({ skill: "loop", args: "30m /pr-watch [PR番号]" })` を呼び出してループを起動
     - ループは30分おきに本コマンドを再実行する。再実行時は `loop_active: true` のためこのステップはスキップされ、1サイクルのみ実行される
4. **author判定（fail-closed）**: `me="$(gh api user -q .login)"`（実認証アカウント。`config/user.json` の `github_username` は使わない）
   - `author.login` と `me` が**ともに非空**で、**大文字小文字を無視して一致**するときのみ **author**（autoFix 可）
   - どちらかが空/null、`me` 取得失敗、不一致 → **reviewer 扱い（push 禁止）**
5. **実行ロック取得（fail-closed）**: `run_id`（ISO8601時刻 + ランダム suffix）を生成し、state を再 Read してから当該PRキーに `active_run_id` / `active_started_at` / `last_run` を Write
   - 既に `active_run_id` があれば「同一PRの `/pr-watch` が実行中」と報告して**終了**（初回実行同士の二重 push 防止）
   - state の再 Read から Write までに `last_run` が変わった場合も、割り込まれたとみなして**終了**
   - 以降、commit/push 直前の state 再 Read で `active_run_id` が自分の `run_id` と一致しなければ push しない

### 1. CIステータス確認

```bash
gh pr checks "$PR" --json name,state,bucket,link,workflow
```

- **判定は `bucket` のみを根拠にする**（`pass` / `fail` / `pending` / `skipping` / `cancel`）。`gh pr checks` は失敗チェックがあると非ゼロ終了する（exit 8 = pending）が、これは**正常**でありエラー扱いしない。exit code で分岐しない
- 分類:
  - 全て `pass`（または `skipping`）→ CIは健全。`pending_streak` を 0 にしてステップ2へ
  - `fail` / `cancel` あり → 下記「CI失敗対応」へ（`pending` が同時にあっても **fail を優先**）
  - `fail` なしで `pending` あり（CI実行中）→ **待たない**。`pending_streak` を +1 して「CI実行中、次サイクルで再確認」と記録しステップ2へ
    - **`pending_streak >= 3`（約90分解消しない）→ CI stuck の可能性として ESCALATE**（report、無限サイクル防止）

#### CI失敗対応（authorのPRのみ。reviewer立場ならスキップしステップ3で報告）

1. 失敗 check が**複数あれば全て**対象。各 `link`（`.../actions/runs/<run-id>/job/<job-id>`）から run-id / job-id を抽出
2. 失敗ログを取得: `gh run view <run-id> --log-failed`（特定ジョブ: `gh run view --job <job-id> --log-failed`）
3. ログから原因を特定して修正（test / lint / typecheck / build 等）。重い修正は `Agent(subagent_type: "codex:codex-rescue")`
4. ローカルで test / lint / typecheck を実行し修正を確認
5. **修正 diff が空、または直前サイクルと同一の修正なら push せず ESCALATE**（無駄な push と修正ループ防止）
6. **write-ahead**: push の**直前**に state を再 Read し、`active_run_id` が自分の `run_id` と一致する場合だけ `ci_fix_attempts[<check名>]` を +1 して **state を Write**、その後 `git commit`（`fix:` 日本語）→ `git push`（force 系不使用）
   - 順序が重要: push は外部副作用なので「ロック確認 + カウンタ確定 → push」とし、push 後に記録漏れが起きてもカウンタが消えないようにする
7. **同一性キー = 失敗 check 名**（check名が動的に変わるCIでは失敗ログ先頭エラーも加味）。`pending` を挟んでもカウンタは保持（連続 fail である必要はない）
8. `ci_fix_attempts[<check名>] >= 2` → その check は ESCALATE（自動修正停止）。**green に戻った check は `ci_fix_attempts` から削除（リセット）**

### 2. レビューコメント確認

- **Draft PR はレビュー対応をスキップ**（CI対応のみ）。Ready for review になった後のサイクルでレビューコメント対応を開始する
- 取得（3ソース。**IDは必ずソース修飾子付きの複合キーで扱う**）:
  ```bash
  gh pr view "$PR" --json reviews,comments,reviewDecision   # reviews=review:<id> / comments=issue:<id>
  gh api repos/{owner}/{repo}/pulls/$PR/comments            # インライン=inline:<id>
  ```
  - 3ソースとも0件 → 未対応なし。ステップ3へ
  - いずれかが**非ゼロ終了（取得失敗）→ 当該サイクルはレビュー判定を保留**（ログのみ。対応しない）
- `processed_comment_ids`（複合キー `issue:<id>` / `review:<id>` / `inline:<id>`）に**無い**新規のみ対象
- 未対応あり（authorのPR）→ pr-review-loop で対応:
  ```
  Workflow({ name: "pr-review-loop", args: { pr: <PR番号>, autoFix: true, maxRounds: 3 } })
  ```
  - 結果 `SHIP` → 修正は push 済み。**pr-review-loop に渡した対象コメントの複合キーを** `processed_comment_ids` に追加（渡した集合と記録する集合を一致させる）
  - `NEEDS_WORK` / `ESCALATE` / `BLOCKED` → 未解決の CRITICAL/IMPORTANT を報告（自動修正を停止）
- reviewer立場のPR → レビューのみ:
  ```
  Workflow({ name: "pr-review-loop", args: { pr: <PR番号>, autoFix: false } })
  ```
  - 結果を **`gh pr comment` で投稿**。本文先頭に固定マーカー `<!-- pr-watch-bot -->` を埋め、**そのマーカーを含む自分の既存コメントのみ更新**（無ければ新規）＝人手のコメントを上書きしない
  - **コードは触らない／push しない／`gh pr review --approve` `--request-changes` はしない**（コメントのみ）

### 3. 状態判定・報告

- **CI全green かつ 未対応レビューなし** → 「[完了] 全チェック通過・レビュー対応完了。これ以上の対応は不要です。`/loop` を `Esc` で停止できます」。**commit / push はしない（no-op）**
- **今サイクルで対応した** → 対応内容（CI修正 / レビュー対応）のサマリーを報告
- **ESCALATE / BLOCKED / NEEDS_WORK（高位指摘が残存）** → 「[要対応] 自動対応の限界に到達。未解決: \<内容\>。人間の判断が必要です」。**いずれの停止系も** Slack通知先（`config/user.json` の `slack.notification_channel`）が設定済みなら通知

### 4. 冪等性（state 記録）

- パス: `.local/pr-watch-state.json`。構造（PR番号をキー）:
  ```json
  {
    "<PR番号>": {
      "loop_active": true,
      "last_ci_buckets": { "<check名>": "pass | fail | pending" },
      "ci_fix_attempts": { "<check名>": 0 },
      "pending_streak": 0,
      "processed_comment_ids": ["issue:<id>", "review:<id>", "inline:<id>"],
      "active_run_id": "<run_id>",
      "active_started_at": "<ISO8601>",
      "last_run": "<ISO8601>"
    }
  }
  ```
- `loop_active`: `true` のとき loop skill の再起動をスキップする（二重起動防止）。PR が CLOSED/MERGED になると当該キーごと削除される
- 値ドメインは `gh pr checks` の `bucket`（pass / fail / pending / skipping / cancel）に統一
- **競合検出（多重起動・fail-closed）**: ステップ0で `active_run_id` を取得し、Write/push の**直前に state を再 Read** する。`active_run_id` が自分の `run_id` と異なる、または `last_run` が想定外に変わっていれば、**自分の Write を破棄し push を見送る**（lost update と二重 push を防ぐ）
- **終了処理**: サイクル終了時に state を再 Read し、`active_run_id` が自分の `run_id` と一致する場合だけ `active_run_id` / `active_started_at` を削除して Write する

## 安全・制約

- 自動push は author のPR限定。**author判定が確定できなければ push しない（fail-closed）**
- `git push --force` / `--force-with-lease` は禁止
- reviewer立場では `gh pr comment`（`<!-- pr-watch-bot -->` マーカー付き冪等更新）のみ可。`gh pr review` / コード変更 / push は禁止
- 1サイクルの自動修正上限: CI修正は check 毎に2回（`ci_fix_attempts`）+ レビュー3ラウンド（pr-review-loop 側で担保）。CI全green後は no-op
- Draft PR は CI対応のみ。Closed / Merged PR は対象外（ステップ0で終了）
- **多重起動・他系統との競合**:
  - team-run Phase 3 で既に同一PRの監視ループを起動済みなら二重に `/loop` を起動しない
  - state の `active_run_id` ロックと Write/push 直前の競合検出（上記）で、ほぼ同時の別ループによる二重 push を抑止する
  - `watch_repos` 配下のPRを `/pr-watch` で能動監視する間は、`scheduled-tasks/pr-review`（毎時バッチ）が同一PRに同時に当たると二重処理になりうる。両者を同一PRに重複させない運用とする（state ファイルは別系統で共有されない）
- `/loop` はセッションが開いている間のみ動作（閉じると停止）。24/7 監視は `scheduled-tasks/pr-review`（毎時バッチ）が担う別系統

## 関連

- `commands/team-run.md` — 実装完了 → PR作成 → 本コマンドで継続監視（Phase 3）
- `workflows/pr-review-loop.js` — レビュー→修正ループ（本コマンドが `name: "pr-review-loop"` で呼ぶ）
- `scheduled-tasks/pr-review/SKILL.md` — 全PR毎時バッチ（役割が異なる別系統）
- `context/loop-engineering.md` — 実行モデルの正典
