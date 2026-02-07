# カスタムPlaywrightコードの実行

CLIコマンドではカバーできない高度なシナリオのために `run-code` を使用して任意のPlaywrightコードを実行する。

## 構文

```bash
playwright-cli run-code "async page => {
  // Playwright コードをここに記述
  // page.context() でブラウザコンテキスト操作にアクセス可能
}"
```

## 位置情報

```bash
# 位置情報の権限を付与して場所を設定
playwright-cli run-code "async page => {
  await page.context().grantPermissions(['geolocation']);
  await page.context().setGeolocation({ latitude: 37.7749, longitude: -122.4194 });
}"

# ロンドンに場所を設定
playwright-cli run-code "async page => {
  await page.context().grantPermissions(['geolocation']);
  await page.context().setGeolocation({ latitude: 51.5074, longitude: -0.1278 });
}"

# 位置情報のオーバーライドをクリア
playwright-cli run-code "async page => {
  await page.context().clearPermissions();
}"
```

## 権限

```bash
# 複数の権限を付与
playwright-cli run-code "async page => {
  await page.context().grantPermissions([
    'geolocation',
    'notifications',
    'camera',
    'microphone'
  ]);
}"

# 特定のオリジンに対して権限を付与
playwright-cli run-code "async page => {
  await page.context().grantPermissions(['clipboard-read'], {
    origin: 'https://example.com'
  });
}"
```

## メディアエミュレーション

```bash
# ダークカラースキームをエミュレート
playwright-cli run-code "async page => {
  await page.emulateMedia({ colorScheme: 'dark' });
}"

# ライトカラースキームをエミュレート
playwright-cli run-code "async page => {
  await page.emulateMedia({ colorScheme: 'light' });
}"

# モーション軽減をエミュレート
playwright-cli run-code "async page => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
}"

# 印刷メディアをエミュレート
playwright-cli run-code "async page => {
  await page.emulateMedia({ media: 'print' });
}"
```

## 待機戦略

```bash
# ネットワークアイドルまで待機
playwright-cli run-code "async page => {
  await page.waitForLoadState('networkidle');
}"

# 特定の要素が表示されるまで待機
playwright-cli run-code "async page => {
  await page.waitForSelector('.loading', { state: 'hidden' });
}"

# 関数がtrueを返すまで待機
playwright-cli run-code "async page => {
  await page.waitForFunction(() => window.appReady === true);
}"

# タイムアウト付き待機
playwright-cli run-code "async page => {
  await page.waitForSelector('.result', { timeout: 10000 });
}"
```

## フレームとiframe

```bash
# iframeを操作
playwright-cli run-code "async page => {
  const frame = page.locator('iframe#my-iframe').contentFrame();
  await frame.locator('button').click();
}"

# 全フレームを取得
playwright-cli run-code "async page => {
  const frames = page.frames();
  return frames.map(f => f.url());
}"
```

## ファイルダウンロード

```bash
# ファイルダウンロードを処理
playwright-cli run-code "async page => {
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.click('a.download-link')
  ]);
  await download.saveAs('./downloaded-file.pdf');
  return download.suggestedFilename();
}"
```

## クリップボード

```bash
# クリップボードを読み取り（権限が必要）
playwright-cli run-code "async page => {
  await page.context().grantPermissions(['clipboard-read']);
  return await page.evaluate(() => navigator.clipboard.readText());
}"

# クリップボードに書き込み
playwright-cli run-code "async page => {
  await page.evaluate(text => navigator.clipboard.writeText(text), 'Hello clipboard!');
}"
```

## ページ情報

```bash
# ページタイトルを取得
playwright-cli run-code "async page => {
  return await page.title();
}"

# 現在のURLを取得
playwright-cli run-code "async page => {
  return page.url();
}"

# ページコンテンツを取得
playwright-cli run-code "async page => {
  return await page.content();
}"

# ビューポートサイズを取得
playwright-cli run-code "async page => {
  return page.viewportSize();
}"
```

## JavaScript実行

```bash
# JavaScriptを実行して結果を返す
playwright-cli run-code "async page => {
  return await page.evaluate(() => {
    return {
      userAgent: navigator.userAgent,
      language: navigator.language,
      cookiesEnabled: navigator.cookieEnabled
    };
  });
}"

# evaluate に引数を渡す
playwright-cli run-code "async page => {
  const multiplier = 5;
  return await page.evaluate(m => document.querySelectorAll('li').length * m, multiplier);
}"
```

## エラーハンドリング

```bash
# run-code でのtry-catch
playwright-cli run-code "async page => {
  try {
    await page.click('.maybe-missing', { timeout: 1000 });
    return 'clicked';
  } catch (e) {
    return 'element not found';
  }
}"
```

## 複雑なワークフロー

```bash
# ログインして状態を保存
playwright-cli run-code "async page => {
  await page.goto('https://example.com/login');
  await page.fill('input[name=email]', 'user@example.com');
  await page.fill('input[name=password]', 'secret');
  await page.click('button[type=submit]');
  await page.waitForURL('**/dashboard');
  await page.context().storageState({ path: 'auth.json' });
  return 'Login successful';
}"

# 複数ページからデータをスクレイピング
playwright-cli run-code "async page => {
  const results = [];
  for (let i = 1; i <= 3; i++) {
    await page.goto(\`https://example.com/page/\${i}\`);
    const items = await page.locator('.item').allTextContents();
    results.push(...items);
  }
  return results;
}"
```
