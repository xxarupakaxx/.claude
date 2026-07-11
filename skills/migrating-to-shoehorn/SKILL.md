---
name: migrating-to-shoehorn
description: テストファイルを `as` 型アサーションから @total-typescript/shoehorn へ移行する。ユーザーが shoehorn に言及した場合、テスト内の `as` を置き換えたい場合、部分的なテストデータが必要な場合に使用する。
---

# Shoehorn へ移行する

## shoehorn を使う理由

`shoehorn` を使うと、TypeScript の型検査を満たしたまま、テストへ部分的なデータを渡せる。
`as` アサーションを型安全な代替手段へ置き換える。

**テストコードだけで使う。**
本番コードでは shoehorn を使わない。

テストで `as` を使う場合には次の問題がある。

- 普段は使わないように訓練されている。
- 対象の型を手動で指定する必要がある。
- 意図的に誤ったデータを渡すには、二重のアサーション（`as unknown as Type`）が必要になる。

## インストール

```bash
npm i @total-typescript/shoehorn
```

## 移行パターン

### 必要なプロパティが少ない大きなオブジェクト

変更前：

```ts
type Request = {
  body: { id: string };
  headers: Record<string, string>;
  cookies: Record<string, string>;
  // ...20 more properties
};

it("gets user by id", () => {
  // Only care about body.id but must fake entire Request
  getUser({
    body: { id: "123" },
    headers: {},
    cookies: {},
    // ...fake all 20 properties
  });
});
```

変更後：

```ts
import { fromPartial } from "@total-typescript/shoehorn";

it("gets user by id", () => {
  getUser(
    fromPartial({
      body: { id: "123" },
    }),
  );
});
```

### `as Type` から `fromPartial()` への移行

変更前：

```ts
getUser({ body: { id: "123" } } as Request);
```

変更後：

```ts
import { fromPartial } from "@total-typescript/shoehorn";

getUser(fromPartial({ body: { id: "123" } }));
```

### `as unknown as Type` から `fromAny()` への移行

変更前：

```ts
getUser({ body: { id: 123 } } as unknown as Request); // wrong type on purpose
```

変更後：

```ts
import { fromAny } from "@total-typescript/shoehorn";

getUser(fromAny({ body: { id: 123 } }));
```

## 関数の使い分け

| 関数 | 用途 |
| --- | --- |
| `fromPartial()` | 型検査を満たす部分的なデータを渡す |
| `fromAny()` | 意図的に誤ったデータを渡す（自動補完は維持される） |
| `fromExact()` | 完全なオブジェクトを強制する（後で fromPartial と交換できる） |

## ワークフロー

1. **要件を集める**。
   - 問題の原因になっている `as` アサーションを含むテストファイルはどれか。
   - 一部のプロパティだけが重要な大きなオブジェクトを扱っているか。
   - エラーをテストするため、意図的に誤ったデータを渡す必要があるか。

2. **インストールして移行する**。
   - [ ] インストールする：`npm i @total-typescript/shoehorn`
   - [ ] `as` アサーションを含むテストファイルを探す：`grep -r " as [A-Z]" --include="*.test.ts" --include="*.spec.ts"`
   - [ ] `as Type` を `fromPartial()` へ置き換える。
   - [ ] `as unknown as Type` を `fromAny()` へ置き換える。
   - [ ] `@total-typescript/shoehorn` からの import を追加する。
   - [ ] 型検査を実行して確認する。
