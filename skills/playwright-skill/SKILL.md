---
name: playwright-skill
description: Playwright による完全なブラウザ自動化。開発サーバーを自動検出し、クリーンなテストスクリプトを /tmp に書き出す。ページのテスト、フォーム入力、スクリーンショット取得、レスポンシブデザイン確認、UX 検証、ログインフロー検証、リンク切れチェック、あらゆるブラウザ作業の自動化に対応。Web サイトをテストしたい、ブラウザ操作を自動化したい、Web 機能を検証したい、またはブラウザベースのテストを行いたい場合に使用する。
---

**重要 - パス解決:**
このスキルは複数の場所（プラグインシステム、手動インストール、グローバル、プロジェクト固有）にインストールされ得る。コマンドを実行する前に、読み込んだこの SKILL.md ファイルの場所に基づいてスキルディレクトリを特定し、以降のすべてのコマンドでそのパスを使うこと。`$SKILL_DIR` は、発見した実際のパスに置き換えること。

一般的なインストールパス:

- プラグインシステム: `~/.claude/plugins/marketplaces/playwright-skill/skills/playwright-skill`
- 手動グローバル: `~/.claude/skills/playwright-skill`
- プロジェクト固有: `<project>/.claude/skills/playwright-skill`

# Playwright ブラウザ自動化

汎用のブラウザ自動化スキル。依頼された自動化タスクのためにカスタム Playwright コードを書き、ユニバーサル実行機構で実行する。

**重要ワークフロー - 次の手順を順番通りに必ず実行する:**

1. **開発サーバーの自動検出** - localhost をテストする場合、必ず最初にサーバー検出を実行する:

   ```bash
   cd $SKILL_DIR && node -e "require('./lib/helpers').detectDevServers().then(servers => console.log(JSON.stringify(servers)))"
````

* **1つ見つかった場合**: 自動的にそれを使い、ユーザーに知らせる
* **複数見つかった場合**: どれをテストするかユーザーに確認する
* **見つからない場合**: URL を尋ねる、または開発サーバーの起動を手伝うと提案する

2. **スクリプトは /tmp に書く** - テストファイルはスキルディレクトリには絶対に書かず、必ず `/tmp/playwright-test-*.js` を使う

3. **デフォルトは可視ブラウザ** - ユーザーが headless を明示しない限り、常に `headless: false` を使う

4. **URL をパラメータ化する** - URL は必ず環境変数か、スクリプト先頭の定数で設定できるようにする

## 仕組み

1. 何をテスト／自動化したいかをユーザーが説明する
2. 実行中の開発サーバーを自動検出する（外部サイトなら URL を尋ねる）
3. `/tmp/playwright-test-*.js` にカスタム Playwright コードを書く（プロジェクトが汚れない）
4. `cd $SKILL_DIR && node run.js /tmp/playwright-test-*.js` で実行する
5. 結果をリアルタイムで表示し、デバッグ用にブラウザも表示する
6. テストファイルは OS により /tmp から自動的にクリーンアップされる

## セットアップ（初回のみ）

```bash
cd $SKILL_DIR
npm run setup
```

Playwright と Chromium ブラウザをインストールする。必要なのは一度だけ。

## 実行パターン

**ステップ1: 開発サーバー検出（localhost テスト用）**

```bash
cd $SKILL_DIR && node -e "require('./lib/helpers').detectDevServers().then(s => console.log(JSON.stringify(s)))"
```

**ステップ2: URL をパラメータ化して /tmp にテストスクリプトを書く**

```javascript
// /tmp/playwright-test-page.js
const { chromium } = require('playwright');

// パラメータ化された URL（検出結果またはユーザー指定）
const TARGET_URL = 'http://localhost:3001'; // <-- 自動検出またはユーザー指定

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  await page.goto(TARGET_URL);
  console.log('ページを読み込みました:', await page.title());

  await page.screenshot({ path: '/tmp/screenshot.png', fullPage: true });
  console.log('📸 スクリーンショットを /tmp/screenshot.png に保存しました');

  await browser.close();
})();
```

**ステップ3: スキルディレクトリから実行する**

```bash
cd $SKILL_DIR && node run.js /tmp/playwright-test-page.js
```

## よくあるパターン

### ページのテスト（複数ビューポート）

```javascript
// /tmp/playwright-test-responsive.js
const { chromium } = require('playwright');

const TARGET_URL = 'http://localhost:3001'; // 自動検出

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const page = await browser.newPage();

  // デスクトップテスト
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.goto(TARGET_URL);
  console.log('Desktop - タイトル:', await page.title());
  await page.screenshot({ path: '/tmp/desktop.png', fullPage: true });

  // モバイルテスト
  await page.setViewportSize({ width: 375, height: 667 });
  await page.screenshot({ path: '/tmp/mobile.png', fullPage: true });

  await browser.close();
})();
```

### ログインフローのテスト

```javascript
// /tmp/playwright-test-login.js
const { chromium } = require('playwright');

const TARGET_URL = 'http://localhost:3001'; // 自動検出

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  await page.goto(`${TARGET_URL}/login`);

  await page.fill('input[name="email"]', 'test@example.com');
  await page.fill('input[name="password"]', 'password123');
  await page.click('button[type="submit"]');

  // リダイレクトを待つ
  await page.waitForURL('**/dashboard');
  console.log('✅ ログイン成功、ダッシュボードへリダイレクトされました');

  await browser.close();
})();
```

### フォーム入力と送信

```javascript
// /tmp/playwright-test-form.js
const { chromium } = require('playwright');

const TARGET_URL = 'http://localhost:3001'; // 自動検出

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 50 });
  const page = await browser.newPage();

  await page.goto(`${TARGET_URL}/contact`);

  await page.fill('input[name="name"]', 'John Doe');
  await page.fill('input[name="email"]', 'john@example.com');
  await page.fill('textarea[name="message"]', 'テストメッセージ');
  await page.click('button[type="submit"]');

  // 送信確認
  await page.waitForSelector('.success-message');
  console.log('✅ フォーム送信に成功しました');

  await browser.close();
})();
```

### リンク切れチェック

```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  await page.goto('http://localhost:3000');

  const links = await page.locator('a[href^="http"]').all();
  const results = { working: 0, broken: [] };

  for (const link of links) {
    const href = await link.getAttribute('href');
    try {
      const response = await page.request.head(href);
      if (response.ok()) {
        results.working++;
      } else {
        results.broken.push({ url: href, status: response.status() });
      }
    } catch (e) {
      results.broken.push({ url: href, error: e.message });
    }
  }

  console.log(`✅ 正常なリンク数: ${results.working}`);
  console.log(`❌ 壊れているリンク:`, results.broken);

  await browser.close();
})();
```

### エラーハンドリング付きスクリーンショット

```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    await page.goto('http://localhost:3000', {
      waitUntil: 'networkidle',
      timeout: 10000,
    });

    await page.screenshot({
      path: '/tmp/screenshot.png',
      fullPage: true,
    });

    console.log('📸 スクリーンショットを /tmp/screenshot.png に保存しました');
  } catch (error) {
    console.error('❌ エラー:', error.message);
  } finally {
    await browser.close();
  }
})();
```

### レスポンシブデザインのテスト

```javascript
// /tmp/playwright-test-responsive-full.js
const { chromium } = require('playwright');

const TARGET_URL = 'http://localhost:3001'; // 自動検出

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  const viewports = [
    { name: 'Desktop', width: 1920, height: 1080 },
    { name: 'Tablet', width: 768, height: 1024 },
    { name: 'Mobile', width: 375, height: 667 },
  ];

  for (const viewport of viewports) {
    console.log(
      `テスト中: ${viewport.name} (${viewport.width}x${viewport.height})`,
    );

    await page.setViewportSize({
      width: viewport.width,
      height: viewport.height,
    });

    await page.goto(TARGET_URL);
    await page.waitForTimeout(1000);

    await page.screenshot({
      path: `/tmp/${viewport.name.toLowerCase()}.png`,
      fullPage: true,
    });
  }

  console.log('✅ 全ビューポートのテストが完了しました');
  await browser.close();
})();
```

## インライン実行（簡単な作業）

ファイルを作らずに、ワンオフのコードをインラインで実行できる:

```bash
# すぐスクリーンショットを撮る
cd $SKILL_DIR && node run.js "
const browser = await chromium.launch({ headless: false });
const page = await browser.newPage();
await page.goto('http://localhost:3001');
await page.screenshot({ path: '/tmp/quick-screenshot.png', fullPage: true });
console.log('Screenshot saved');
await browser.close();
"
```

**インラインとファイルの使い分け:**

* **インライン**: 単発の簡易作業（スクショ、要素の有無、タイトル取得など）
* **ファイル**: 複雑なテスト、レスポンシブ確認、再実行したくなる作業全般

## 利用可能なヘルパー

`lib/helpers.js` にある任意のユーティリティ関数:

```javascript
const helpers = require('./lib/helpers');

// 実行中の開発サーバー検出（重要 - 最初にこれを使う！）
const servers = await helpers.detectDevServers();
console.log('見つかったサーバー:', servers);

// リトライ付き安全クリック
await helpers.safeClick(page, 'button.submit', { retries: 3 });

// クリア付き安全タイピング
await helpers.safeType(page, '#username', 'testuser');

// タイムスタンプ付きスクリーンショット
await helpers.takeScreenshot(page, 'test-result');

// Cookie バナー対応
await helpers.handleCookieBanner(page);

// テーブルデータ抽出
const data = await helpers.extractTableData(page, 'table.results');
```

全リストは `lib/helpers.js` を参照。

## カスタム HTTP ヘッダー

環境変数で、すべての HTTP リクエストにカスタムヘッダーを設定できる。用途例:

* バックエンド側で自動化トラフィックを識別する
* LLM 最適化されたレスポンスを受け取る（装飾 HTML ではなくプレーンテキストエラーなど）
* 認証トークンをグローバルに付与する

### 設定

**単一ヘッダー（一般的）:**

```bash
PW_HEADER_NAME=X-Automated-By PW_HEADER_VALUE=playwright-skill \
  cd $SKILL_DIR && node run.js /tmp/my-script.js
```

**複数ヘッダー（JSON 形式）:**

```bash
PW_EXTRA_HEADERS='{"X-Automated-By":"playwright-skill","X-Debug":"true"}' \
  cd $SKILL_DIR && node run.js /tmp/my-script.js
```

### 仕組み

`helpers.createContext()` を使うとヘッダーが自動適用される:

```javascript
const context = await helpers.createContext(browser);
const page = await context.newPage();
// この page からのすべてのリクエストにカスタムヘッダーが付く
```

素の Playwright API を使うスクリプトでは、注入される `getContextOptionsWithHeaders()` を使う:

```javascript
const context = await browser.newContext(
  getContextOptionsWithHeaders({ viewport: { width: 1920, height: 1080 } }),
);
```

## 高度な使い方

Playwright API の包括的ドキュメントは [API_REFERENCE.md](API_REFERENCE.md) を参照:

* セレクタ／ロケータのベストプラクティス
* ネットワークのインターセプトと API モック
* 認証とセッション管理
* ビジュアルリグレッションテスト
* モバイル端末のエミュレーション
* パフォーマンステスト
* デバッグ手法
* CI/CD 統合

## Tips

* **重要: まずサーバー検出** - localhost テストでは、コードを書く前に必ず `detectDevServers()` を実行する
* **カスタムヘッダー** - `PW_HEADER_NAME` / `PW_HEADER_VALUE` で自動化トラフィックを識別できる
* **テストファイルは /tmp** - `/tmp/playwright-test-*.js` を使い、スキルディレクトリやプロジェクトには書かない
* **URL をパラメータ化** - 検出／指定 URL は各スクリプト先頭の `TARGET_URL` 定数に置く
* **デフォルトは可視ブラウザ** - headless を明示されない限り `headless: false`
* **headless モード** - ユーザーが「headless」や「バックグラウンド」を明示したときのみ `headless: true`
* **減速**: `slowMo: 100` で操作を見やすくする
* **待ち戦略**: 固定 sleep ではなく `waitForURL` / `waitForSelector` / `waitForLoadState` を使う
* **エラーハンドリング**: 堅牢な自動化のために try-catch を使う
* **進捗ログ**: `console.log()` で進捗と状況を出力する

## トラブルシューティング

**Playwright が未インストール:**

```bash
cd $SKILL_DIR && npm run setup
```

**Module not found:**
`run.js` ラッパー経由で、スキルディレクトリから実行していることを確認する

**ブラウザが開かない:**
`headless: false` を確認し、表示環境があることを確認する

**要素が見つからない:**
待ちを追加する: `await page.waitForSelector('.element', { timeout: 10000 })`

## 使用例

```
ユーザー:「マーケティングページがいい感じに見えるかテストして」

Claude: 複数ビューポートでマーケティングページをテストします。まず実行中サーバーを検出します…
[detectDevServers() を実行]
[出力: ポート 3001 でサーバー発見]
http://localhost:3001 で開発サーバーが動いているのを見つけました

[/tmp/playwright-test-marketing.js に URL をパラメータ化してカスタムスクリプトを書き込み]
[cd $SKILL_DIR && node run.js /tmp/playwright-test-marketing.js を実行]
[/tmp/ のスクリーンショット付きで結果を表示]
```

```
ユーザー:「ログイン後に正しくリダイレクトされるか確認して」

Claude: ログインフローをテストします。まず実行中サーバーを確認します…
[detectDevServers() を実行]
[出力: ポート 3000 と 3001 を発見]
開発サーバーが2つ見つかりました。どちらをテストしますか？
- http://localhost:3000
- http://localhost:3001

ユーザー:「3001で」

[/tmp/playwright-test-login.js にログイン自動化を書き込み]
[cd $SKILL_DIR && node run.js /tmp/playwright-test-login.js を実行]
[結果: ✅ ログイン成功、/dashboard へリダイレクト]
```

## 注記

* 自動化はリクエストごとにカスタムで作成する
* 事前用意されたスクリプトに限定されず、あらゆるブラウザ作業が可能
* 実行中の開発サーバーを自動検出し、URL のハードコードを避ける
* テストスクリプトは `/tmp` に書き、プロジェクトを汚さない
* `run.js` 経由の適切なモジュール解決で安定実行できる
* 段階的な開示：高度な機能が必要なときだけ API_REFERENCE.md を読み込む

```
