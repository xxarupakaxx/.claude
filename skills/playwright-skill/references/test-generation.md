# テスト生成

ブラウザを操作するだけで、Playwrightのテストコードを自動的に生成する。

## 仕組み

`playwright-cli` で実行するすべてのアクションが、対応するPlaywright TypeScriptコードを生成する。
このコードは出力に表示され、テストファイルに直接コピーできる。

## ワークフロー例

```bash
# セッションを開始
playwright-cli open https://example.com/login

# スナップショットで要素を確認
playwright-cli snapshot
# 出力: e1 [textbox "Email"], e2 [textbox "Password"], e3 [button "Sign In"]

# フォームフィールドを入力 - コードが自動生成される
playwright-cli fill e1 "user@example.com"
# 実行されたPlaywrightコード:
# await page.getByRole('textbox', { name: 'Email' }).fill('user@example.com');

playwright-cli fill e2 "password123"
# 実行されたPlaywrightコード:
# await page.getByRole('textbox', { name: 'Password' }).fill('password123');

playwright-cli click e3
# 実行されたPlaywrightコード:
# await page.getByRole('button', { name: 'Sign In' }).click();
```

## テストファイルの構築

生成されたコードをPlaywrightテストに集約する:

```typescript
import { test, expect } from '@playwright/test';

test('ログインフロー', async ({ page }) => {
  // playwright-cli セッションから生成されたコード:
  await page.goto('https://example.com/login');
  await page.getByRole('textbox', { name: 'Email' }).fill('user@example.com');
  await page.getByRole('textbox', { name: 'Password' }).fill('password123');
  await page.getByRole('button', { name: 'Sign In' }).click();

  // アサーションを追加
  await expect(page).toHaveURL(/.*dashboard/);
});
```

## ベストプラクティス

### 1. セマンティックロケーターを使用する

生成されたコードは可能な限りロールベースのロケーターを使用し、変更に強い:

```typescript
// 生成されたコード（良い例 - セマンティック）
await page.getByRole('button', { name: 'Submit' }).click();

// 避ける（脆い - CSSセレクタ）
await page.locator('#submit-btn').click();
```

### 2. 操作前にページ構造を確認する

アクションを記録する前にスナップショットでページ構造を理解する:

```bash
playwright-cli open https://example.com
playwright-cli snapshot
# 要素構造を確認
playwright-cli click e5
```

### 3. アサーションは手動で追加する

生成されたコードはアクションのみをキャプチャし、アサーションは含まない。テストに期待値を追加する:

```typescript
// 生成されたアクション
await page.getByRole('button', { name: 'Submit' }).click();

// 手動で追加するアサーション
await expect(page.getByText('Success')).toBeVisible();
```
