# ブラウザセッション管理

状態の永続化が可能な、複数の独立したブラウザセッションを同時に実行する。

## 名前付きブラウザセッション

`-s` フラグでブラウザコンテキストを分離:

```bash
# ブラウザ1: 認証フロー
playwright-cli -s=auth open https://app.example.com/login

# ブラウザ2: パブリックブラウジング（別のCookie・ストレージ）
playwright-cli -s=public open https://example.com

# コマンドはブラウザセッションごとに分離される
playwright-cli -s=auth fill e1 "user@example.com"
playwright-cli -s=public snapshot
```

## ブラウザセッションの分離特性

各ブラウザセッションは以下が独立:
- Cookie
- LocalStorage / SessionStorage
- IndexedDB
- キャッシュ
- ブラウジング履歴
- 開いているタブ

## ブラウザセッションコマンド

```bash
# 全ブラウザセッションを一覧表示
playwright-cli list

# ブラウザセッションを停止（ブラウザを閉じる）
playwright-cli close                # デフォルトブラウザを停止
playwright-cli -s=mysession close   # 名前付きブラウザを停止

# 全ブラウザセッションを停止
playwright-cli close-all

# 全デーモンプロセスを強制終了（停滞・ゾンビプロセス用）
playwright-cli kill-all

# ブラウザセッションのユーザーデータを削除（プロファイルディレクトリ）
playwright-cli delete-data                # デフォルトブラウザデータを削除
playwright-cli -s=mysession delete-data   # 名前付きブラウザデータを削除
```

## 環境変数

環境変数でデフォルトのブラウザセッション名を設定:

```bash
export PLAYWRIGHT_CLI_SESSION="mysession"
playwright-cli open example.com  # 自動的に"mysession"を使用
```

## よくあるパターン

### 同時スクレイピング

```bash
#!/bin/bash
# 複数サイトを並行してスクレイピング

# 全ブラウザを起動
playwright-cli -s=site1 open https://site1.com &
playwright-cli -s=site2 open https://site2.com &
playwright-cli -s=site3 open https://site3.com &
wait

# 各ブラウザからスナップショットを取得
playwright-cli -s=site1 snapshot
playwright-cli -s=site2 snapshot
playwright-cli -s=site3 snapshot

# クリーンアップ
playwright-cli close-all
```

### A/Bテストセッション

```bash
# 異なるユーザー体験をテスト
playwright-cli -s=variant-a open "https://app.com?variant=a"
playwright-cli -s=variant-b open "https://app.com?variant=b"

# 比較
playwright-cli -s=variant-a screenshot
playwright-cli -s=variant-b screenshot
```

### 永続プロファイル

デフォルトでは、ブラウザプロファイルはメモリ上にのみ保持される。`--persistent` フラグを `open` で使用してプロファイルをディスクに永続化:

```bash
# 永続プロファイルを使用（自動生成されたパス）
playwright-cli open https://example.com --persistent

# カスタムディレクトリで永続プロファイルを使用
playwright-cli open https://example.com --profile=/path/to/profile
```

## デフォルトブラウザセッション

`-s` を省略すると、コマンドはデフォルトブラウザセッションを使用:

```bash
# 同じデフォルトブラウザセッションを使用
playwright-cli open https://example.com
playwright-cli snapshot
playwright-cli close  # デフォルトブラウザを停止
```

## ブラウザセッションの設定

セッション起動時に特定の設定を適用:

```bash
# 設定ファイルで開く
playwright-cli open https://example.com --config=.playwright/my-cli.json

# 特定のブラウザで開く
playwright-cli open https://example.com --browser=firefox

# ヘッド付きモードで開く
playwright-cli open https://example.com --headed

# 永続プロファイルで開く
playwright-cli open https://example.com --persistent
```

## ベストプラクティス

### 1. セッション名は意味のある名前を付ける

```bash
# 良い例: 目的が明確
playwright-cli -s=github-auth open https://github.com
playwright-cli -s=docs-scrape open https://docs.example.com

# 避ける: 汎用的な名前
playwright-cli -s=s1 open https://github.com
```

### 2. 必ずクリーンアップする

```bash
# 完了時にブラウザを停止
playwright-cli -s=auth close
playwright-cli -s=scrape close

# または一括停止
playwright-cli close-all

# ブラウザが応答しなくなった場合やゾンビプロセスが残った場合
playwright-cli kill-all
```

### 3. 古いブラウザデータを削除する

```bash
# ディスク容量を確保するために古いブラウザデータを削除
playwright-cli -s=oldsession delete-data
```
