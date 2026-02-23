---
name: playwright-skill
description: playwright-cli によるブラウザ自動化。CLIコマンドでブラウザ操作（クリック、入力、スクリーンショット、ネットワークモック等）を実行する。Webサイトのテスト、フォーム入力、スクリーンショット取得、レスポンシブ確認、UX検証、ログインフロー検証、リンク切れチェック、あらゆるブラウザ作業の自動化に対応。Webサイトをテストしたい、ブラウザ操作を自動化したい、Web機能を検証したい、またはブラウザベースのテストを行いたい場合に使用する。
allowed-tools: Bash, Read
---

# playwright-cli によるブラウザ自動化

## クイックスタート

```bash
# 新しいブラウザを開く
playwright-cli open
# ページに移動
playwright-cli goto https://playwright.dev
# スナップショットで取得した参照IDを使ってページを操作
playwright-cli click e15
playwright-cli type "page.click"
playwright-cli press Enter
# スクリーンショットを撮る
playwright-cli screenshot
# ブラウザを閉じる
playwright-cli close
```

## ファイル出力先ルール（IMPORTANT）

**タスク作業中（メモリディレクトリが存在する場合）**、スクリーンショット・PDF・ビデオ・トレース等のファイル出力先は、現在のタスクのメモリディレクトリに保存する。

```bash
# 保存先: ${MEMORY_DIR}/memory/YYMMDD_<task_name>/
# 例: .local/memory/260207_login-test/

playwright-cli screenshot --filename=${MEMORY_DIR}/memory/YYMMDD_<task_name>/screenshot-top.png
playwright-cli screenshot e5 --filename=${MEMORY_DIR}/memory/YYMMDD_<task_name>/screenshot-element.png
playwright-cli pdf --filename=${MEMORY_DIR}/memory/YYMMDD_<task_name>/page.pdf
playwright-cli video-stop ${MEMORY_DIR}/memory/YYMMDD_<task_name>/recording.webm
playwright-cli snapshot --filename=${MEMORY_DIR}/memory/YYMMDD_<task_name>/snapshot.yaml
playwright-cli state-save ${MEMORY_DIR}/memory/YYMMDD_<task_name>/auth-state.json
```

**命名規則:**
- スクリーンショット: `screenshot-<用途>.png`（例: `screenshot-top.png`, `screenshot-mobile.png`, `screenshot-after-login.png`）
- PDF: `<ページ名>.pdf`
- ビデオ: `recording-<内容>.webm`
- スナップショット: `snapshot-<ステップ>.yaml`
- ストレージ状態: `state-<用途>.json`

**タスク外（メモリディレクトリがない場合）**: `/tmp/` に保存する。

## コマンド一覧

→ `Read references/command-reference.md` を参照

## 使用例

→ `Read references/usage-examples.md` を参照

## 詳細トピック

* **リクエストモック** [references/request-mocking.md](references/request-mocking.md)
* **カスタムPlaywrightコードの実行** [references/running-code.md](references/running-code.md)
* **ブラウザセッション管理** [references/session-management.md](references/session-management.md)
* **ストレージ状態（Cookie、localStorage）** [references/storage-state.md](references/storage-state.md)
* **テスト生成** [references/test-generation.md](references/test-generation.md)
* **トレーシング** [references/tracing.md](references/tracing.md)
* **ビデオ録画** [references/video-recording.md](references/video-recording.md)
