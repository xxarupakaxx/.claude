# リクエストモック

ネットワークリクエストのインターセプト、モック、変更、ブロックを行う。

## CLI Route コマンド

```bash
# カスタムステータスでモック
playwright-cli route "**/*.jpg" --status=404

# JSONボディでモック
playwright-cli route "**/api/users" --body='[{"id":1,"name":"Alice"}]' --content-type=application/json

# カスタムヘッダー付きでモック
playwright-cli route "**/api/data" --body='{"ok":true}' --header="X-Custom: value"

# リクエストからヘッダーを除去
playwright-cli route "**/*" --remove-header=cookie,authorization

# 有効なルートを一覧表示
playwright-cli route-list

# ルートを削除（個別または全て）
playwright-cli unroute "**/*.jpg"
playwright-cli unroute
```

## URLパターン

```
**/api/users           - パスの完全一致
**/api/*/details       - パス内のワイルドカード
**/*.{png,jpg,jpeg}    - ファイル拡張子の一致
**/search?q=*          - クエリパラメータの一致
```

## run-code による高度なモック

条件付きレスポンス、リクエストボディの検査、レスポンスの変更、遅延などに対応。

### リクエストに基づく条件付きレスポンス

```bash
playwright-cli run-code "async page => {
  await page.route('**/api/login', route => {
    const body = route.request().postDataJSON();
    if (body.username === 'admin') {
      route.fulfill({ body: JSON.stringify({ token: 'mock-token' }) });
    } else {
      route.fulfill({ status: 401, body: JSON.stringify({ error: 'Invalid' }) });
    }
  });
}"
```

### 実際のレスポンスを変更

```bash
playwright-cli run-code "async page => {
  await page.route('**/api/user', async route => {
    const response = await route.fetch();
    const json = await response.json();
    json.isPremium = true;
    await route.fulfill({ response, json });
  });
}"
```

### ネットワーク障害のシミュレーション

```bash
playwright-cli run-code "async page => {
  await page.route('**/api/offline', route => route.abort('internetdisconnected'));
}"
# オプション: connectionrefused, timedout, connectionreset, internetdisconnected
```

### 遅延レスポンス

```bash
playwright-cli run-code "async page => {
  await page.route('**/api/slow', async route => {
    await new Promise(r => setTimeout(r, 3000));
    route.fulfill({ body: JSON.stringify({ data: 'loaded' }) });
  });
}"
```
