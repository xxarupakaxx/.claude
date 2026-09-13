---
name: playwright-skill
description: "`playwright-cli`でWebページを操作・検証する。ユーザーがブラウザ自動化、フォーム/ログイン検証、screenshot、responsive/UX確認、link切れ、request mockingを依頼したときに使う。"
allowed-tools: Bash, Read
---

# playwright-cli

CLIのsnapshotで要素IDを確認し、対象ページだけを操作する。表示・読み取りの確認と、フォーム送信・データ変更・購入などの外部writeを分け、後者はユーザーの明示した対象・範囲・操作に限る。

## 基本操作

```bash
playwright-cli open <url>
playwright-cli goto <url>
playwright-cli snapshot
playwright-cli click <element-id>
playwright-cli fill <element-id> "<value>"
playwright-cli press <key>
playwright-cli screenshot
playwright-cli close
```

snapshotを読み、古い要素IDや推測したselectorを使わない。コマンドの詳細は `references/command-reference.md`、代表例は `references/usage-examples.md` を必要な場合だけ読む。

## headedとsession

ログイン画面の確認やdebugだけ `--headed` を付ける。ログイン状態を再利用する場合は、ユーザーが許可したprofileまたは一時的なstate fileを使う。

```bash
playwright-cli open https://app.example.com/login --headed
playwright-cli snapshot
playwright-cli fill <user-id> "$USER_EMAIL"
playwright-cli fill <password-id> "$USER_PASSWORD"
playwright-cli click <submit-id>
playwright-cli state-save <task-memory>/auth-state.json
playwright-cli open https://app.example.com
playwright-cli state-load <task-memory>/auth-state.json
```

password、token、cookie、localStorageなどのsecretを会話・ログ・commitへ出さない。認証stateはrepoへ置かず `.gitignore` 対象のtask memoryまたは一時pathへ保存し、不要になったら削除する。永続profile（`--persistent`）は保存範囲を説明できる場合だけ使う。session管理の細則は `references/session-management.md` と `references/storage-state.md` を読む。

## artifactの保存

task memoryがある場合、screenshot、PDF、video、trace、snapshot、auth stateは `${MEMORY_DIR}/memory/YYMMDD_<task_name>/` 配下へ保存する。task memoryがなければ `/tmp/` を使う。用途が分かる名前（`screenshot-<用途>.png`、`<page>.pdf`、`recording-<内容>.webm`、`snapshot-<step>.yaml`）にし、秘密や不要なrawデータを残さない。

```bash
playwright-cli screenshot --filename=<task-memory>/screenshot-top.png
playwright-cli pdf --filename=<task-memory>/page.pdf
playwright-cli video-stop <task-memory>/recording.webm
playwright-cli snapshot --filename=<task-memory>/snapshot.yaml
```

## 条件付きの詳細

目的に応じて必要なreferenceだけ読む。

| 目的 | 参照 |
| --- | --- |
| request mocking | `references/request-mocking.md` |
| page内コード | `references/running-code.md` |
| storage/auth | `references/storage-state.md`、`session-management.md` |
| test生成 | `references/test-generation.md` |
| trace | `references/tracing.md` |
| video | `references/video-recording.md` |

## 完了確認

- 対象URL、操作、期待結果、実際の結果を分けて記録する。
- 外部writeの送信前に、対象と入力を再確認する。削除、課金、権限変更、公開、メール送信は明示依頼なしに確定しない。
- screenshotやtraceは必要な画面だけを取り、認証情報を含むものを共有しない。
- 未接続、ログイン失敗、要素不在、ネットワーク失敗を成功扱いせず、再現条件と残る状態を報告する。
