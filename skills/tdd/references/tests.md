# Tests: 粒度・命名・構成

## 粒度

### 1テスト1アサーション原則

```ts
// Bad: 複数の振る舞いを1テストで検証
it("works", () => {
  expect(sum([1,2])).toBe(3);
  expect(sum([])).toBe(0);
  expect(() => sum(null)).toThrow();
});

// Good: 振る舞いごとに分離
it("空配列なら 0 を返すべき", () => {
  expect(sum([])).toBe(0);
});

it("正数の合計を返すべき", () => {
  expect(sum([1, 2, 3])).toBe(6);
});

it("null には InvalidInputError を投げるべき", () => {
  expect(() => sum(null)).toThrow(InvalidInputError);
});
```

「1アサーション」は厳密ではなく、**1つの観測可能な振る舞い** を意味する。
状態の確認に複数 `expect` が必要ならOK。

## 命名

### 「〜すべき」形式

`~/.claude/rules/testing.md` 準拠:

```
describe("calculateTax", () => {
  it("ゼロ金額には課税しないべき", () => { ... });
  it("免税対象には課税しないべき", () => { ... });
  it("標準税率を適用すべき", () => { ... });
  it("国境跨ぎでは輸入税も加算すべき", () => { ... });
});
```

### 「what + given + then」フォーマット（より明示的）

```
it("[条件] のとき [対象] は [結果] すべき")
```

例: `it("負数が混在するとき sum は InvalidInputError を投げるべき")`

## 構成: AAA パターン

```ts
it("既存ユーザーのメール変更は通知メールを送るべき", () => {
  // Arrange
  const user = createUser({ email: "old@example.com" });
  const mailer = new FakeMailer();
  const service = new UserService(repo, mailer);

  // Act
  service.updateEmail(user.id, "new@example.com");

  // Assert
  expect(mailer.sent).toHaveLength(1);
  expect(mailer.sent[0].to).toBe("old@example.com");
});
```

各セクションの間に**空行**を入れて視覚的に区切る。

## 順序

### 依存少 → 多

1. **trivial**: 空入力、null、1件
2. **happy path**: 主要な正常系
3. **edge**: 境界値（0, 最大値, 空文字, 単一要素）
4. **error**: 不正入力、外部依存失敗

### Triangulation

複数の具体例から一般則を導く:

```ts
// 1サイクル目: ハードコードでも通る
it("[1] の合計は 1", () => expect(sum([1])).toBe(1));

// 2サイクル目: ハードコードが破綻 → 一般化を強制
it("[1, 2] の合計は 3", () => expect(sum([1, 2])).toBe(3));

// 3サイクル目: 一般実装の確認
it("[1, 2, 3] の合計は 6", () => expect(sum([1, 2, 3])).toBe(6));
```

## テストの独立性

- `beforeEach` で状態リセット
- グローバル変数を使わない
- 並列実行で壊れないこと（DB接続なら別schemaで）

## 禁止事項（ruleと整合）

- `skip`/`only` のコミット
- 時間依存テスト（`Date.now()` 直接使用 → `clock` 注入で対応）
- 過度なモック（実装詳細への依存）
