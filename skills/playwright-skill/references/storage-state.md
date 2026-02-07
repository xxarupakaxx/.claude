# ストレージ管理

Cookie、localStorage、sessionStorage、IndexedDBを含むブラウザストレージの操作。

## ストレージ状態の保存と復元

```bash
# ブラウザの完全な状態を保存（Cookie + localStorage）
playwright-cli state-save
playwright-cli state-save auth.json

# 保存した状態を復元
playwright-cli state-load auth.json
```

## Cookie操作

```bash
# 全Cookieを一覧表示
playwright-cli cookie-list

# ドメインでフィルタ
playwright-cli cookie-list --domain=example.com

# 特定のCookieを取得
playwright-cli cookie-get session_id

# Cookieを設定（基本）
playwright-cli cookie-set session_id abc123

# Cookieを設定（オプション付き）
playwright-cli cookie-set session_id abc123 --domain=example.com --httpOnly --secure

# Cookieを削除
playwright-cli cookie-delete session_id

# 全Cookieをクリア
playwright-cli cookie-clear
```

## localStorage操作

```bash
# 全アイテムを一覧表示
playwright-cli localstorage-list

# 値を取得
playwright-cli localstorage-get theme

# 値を設定
playwright-cli localstorage-set theme dark

# アイテムを削除
playwright-cli localstorage-delete theme

# 全てクリア
playwright-cli localstorage-clear
```

## sessionStorage操作

```bash
# 全アイテムを一覧表示
playwright-cli sessionstorage-list

# 値を取得
playwright-cli sessionstorage-get step

# 値を設定
playwright-cli sessionstorage-set step 3

# アイテムを削除
playwright-cli sessionstorage-delete step

# 全てクリア
playwright-cli sessionstorage-clear
```

## IndexedDB操作（run-code使用）

```bash
# データベースを一覧表示
playwright-cli run-code "async page => {
  return await page.evaluate(() => {
    return indexedDB.databases ? indexedDB.databases() : 'databases() not supported';
  });
}"

# データベースを削除
playwright-cli run-code "async page => {
  await page.evaluate(name => {
    indexedDB.deleteDatabase(name);
  }, 'my-database');
}"
```

## 認証状態の再利用パターン

一度ログインして状態を保存し、以降のセッションで再利用:

```bash
# 1. ログイン
playwright-cli open https://example.com/login
playwright-cli fill e1 "user@example.com"
playwright-cli fill e2 "password123"
playwright-cli click e3

# 2. 状態を保存
playwright-cli state-save auth.json

# 3. 別のセッションで復元
playwright-cli open https://example.com
playwright-cli state-load auth.json
# ログイン済み状態でアクセス可能
```

## セキュリティに関する注意

- 認証トークンを含むストレージ状態ファイルをコミットしない
- 認証状態ファイルを `.gitignore` に追加する
- 自動化完了後は状態ファイルを削除する
- 機密情報は環境変数を使用する
- センシティブな操作にはインメモリセッションモードが安全
