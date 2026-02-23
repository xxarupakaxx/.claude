# コマンドリファレンス

## コア操作

```bash
playwright-cli open
# URL指定で開く
playwright-cli open https://example.com/
playwright-cli goto https://playwright.dev
playwright-cli type "検索クエリ"
playwright-cli click e3
playwright-cli dblclick e7
playwright-cli fill e5 "user@example.com"
playwright-cli drag e2 e8
playwright-cli hover e4
playwright-cli select e9 "option-value"
playwright-cli upload ./document.pdf
playwright-cli check e12
playwright-cli uncheck e12
playwright-cli snapshot
playwright-cli snapshot --filename=after-click.yaml
playwright-cli eval "document.title"
playwright-cli eval "el => el.textContent" e5
playwright-cli dialog-accept
playwright-cli dialog-accept "確認テキスト"
playwright-cli dialog-dismiss
playwright-cli resize 1920 1080
playwright-cli close
```

## ナビゲーション

```bash
playwright-cli go-back
playwright-cli go-forward
playwright-cli reload
```

## キーボード

```bash
playwright-cli press Enter
playwright-cli press ArrowDown
playwright-cli keydown Shift
playwright-cli keyup Shift
```

## マウス

```bash
playwright-cli mousemove 150 300
playwright-cli mousedown
playwright-cli mousedown right
playwright-cli mouseup
playwright-cli mouseup right
playwright-cli mousewheel 0 100
```

## 保存

```bash
playwright-cli screenshot
playwright-cli screenshot e5
playwright-cli screenshot --filename=page.png
playwright-cli pdf --filename=page.pdf
```

## タブ

```bash
playwright-cli tab-list
playwright-cli tab-new
playwright-cli tab-new https://example.com/page
playwright-cli tab-close
playwright-cli tab-close 2
playwright-cli tab-select 0
```

## ストレージ

```bash
playwright-cli state-save
playwright-cli state-save auth.json
playwright-cli state-load auth.json

# Cookie
playwright-cli cookie-list
playwright-cli cookie-list --domain=example.com
playwright-cli cookie-get session_id
playwright-cli cookie-set session_id abc123
playwright-cli cookie-set session_id abc123 --domain=example.com --httpOnly --secure
playwright-cli cookie-delete session_id
playwright-cli cookie-clear

# LocalStorage
playwright-cli localstorage-list
playwright-cli localstorage-get theme
playwright-cli localstorage-set theme dark
playwright-cli localstorage-delete theme
playwright-cli localstorage-clear

# SessionStorage
playwright-cli sessionstorage-list
playwright-cli sessionstorage-get step
playwright-cli sessionstorage-set step 3
playwright-cli sessionstorage-delete step
playwright-cli sessionstorage-clear
```

## ネットワーク

```bash
playwright-cli route "**/*.jpg" --status=404
playwright-cli route "https://api.example.com/**" --body='{"mock": true}'
playwright-cli route-list
playwright-cli unroute "**/*.jpg"
playwright-cli unroute
```

## 開発者ツール

```bash
playwright-cli console
playwright-cli console warning
playwright-cli network
playwright-cli run-code "async page => await page.context().grantPermissions(['geolocation'])"
playwright-cli tracing-start
playwright-cli tracing-stop
playwright-cli video-start
playwright-cli video-stop video.webm
```

## インストール

```bash
playwright-cli install --skills
playwright-cli install-browser
```

## 設定

```bash
# セッション作成時に特定のブラウザを使用
playwright-cli open --browser=chrome
playwright-cli open --browser=firefox
playwright-cli open --browser=webkit
playwright-cli open --browser=msedge
# 拡張機能経由でブラウザに接続
playwright-cli open --extension

# 永続プロファイルを使用（デフォルトはインメモリ）
playwright-cli open --persistent
# カスタムディレクトリで永続プロファイルを使用
playwright-cli open --profile=/path/to/profile

# 設定ファイルで起動
playwright-cli open --config=my-config.json

# ブラウザを閉じる
playwright-cli close
# デフォルトセッションのユーザーデータを削除
playwright-cli delete-data
```

## ブラウザセッション

```bash
# "mysession"という名前で永続プロファイル付きの新しいブラウザセッションを作成
playwright-cli -s=mysession open example.com --persistent
# プロファイルディレクトリを手動指定する場合（明示的に要求された場合に使用）
playwright-cli -s=mysession open example.com --profile=/path/to/profile
playwright-cli -s=mysession click e6
playwright-cli -s=mysession close  # 名前付きブラウザを停止
playwright-cli -s=mysession delete-data  # 永続セッションのユーザーデータを削除

playwright-cli list
# 全ブラウザを閉じる
playwright-cli close-all
# 全ブラウザプロセスを強制終了
playwright-cli kill-all
```
