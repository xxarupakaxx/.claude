# Interface Design in TDD

## TDD は「使われる側」を先に書く

`it("...", () => { service.foo(...) })` を書いた瞬間、
あなたは **service.foo の最初の利用者** になっている。

→ テストは **Interface のドラフト**。テスト1個 = Interface 1案。

## テストを書きながら Interface を磨く

### Step 1: 理想のテストを書く

「実装が **存在するなら**、こう書きたい」を先に書く:

```ts
it("注文確定時に在庫が引き当てられるべき", async () => {
  const result = await orderService.confirm({
    orderId: "o-1",
    paymentMethod: "credit_card",
  });

  expect(result.status).toBe("confirmed");
  expect(result.reservedStock).toEqual([{ sku: "A", qty: 2 }]);
});
```

### Step 2: 違和感をメモ

テストを書きながら気持ち悪い箇所を控える:
- 引数が多い → Value Object に集約？
- 戻り値が貧弱 → 結果に意味のあるデータを足す？
- Mock 引数が増える → Seam の切り方を見直す？

これらは **Refactor フェーズで対応**。Greenまでは妥協してOK。

### Step 3: 並列で複数案

Interface に確信が持てないなら `design-an-interface` スキルを使い、3+案を並列生成して比較する。

## Interface の3原則

### 1. 小さい

公開メソッド数を最小化:
- 「複数のメソッドの組み合わせで使う」と利用者に強いない
- 「典型的ユースケース1つを1メソッドで」を意識

### 2. 強い（Strong Type）

```ts
// Weak
service.create(name: string, type: string, options: Record<string, any>)

// Strong
service.createUser(req: CreateUserRequest): Promise<User>
```

型で意味を表現する。`string` の壁は薄い。

### 3. 自己説明的

メソッド名を見れば何をするか分かる:

```ts
// Bad
process(data)
handle(input)
execute(command)

// Good
calculateTax(invoice)
sendVerificationEmail(user)
reserveStock(orderItems)
```

## Constructor の設計

### 依存は Constructor Injection

```ts
class TokenService {
  constructor(
    private repo: TokenRepo,
    private clock: Clock,
    private signer: Signer,
  ) {}
}
```

→ Seam が Constructor に集約される。テストで簡単に差し替え可能。

### Optional vs Required の判断

- **常に必要な依存** → required
- **デフォルト挙動でOKな依存** → optional + sensible default

```ts
constructor(
  private repo: TokenRepo,                      // required
  private clock: Clock = systemClock,           // optional (default OK)
) {}
```

## 戻り値の設計

### 1. 失敗の表現

| 言語 | 推奨 |
|------|------|
| TypeScript | `Result<T, E>` 型 or タグ付きunion or `throw` |
| Go | `(T, error)` |
| Rust | `Result<T, E>` |

例外は **想定外** にだけ使う（バリデーション失敗は戻り値で）。

### 2. 集約された結果

```ts
// Bad: 利用者が複数getterを呼ぶ
const status = service.getStatus(id);
const stock = service.getStock(id);
const total = service.getTotal(id);

// Good: 1つの結果に集約
const summary = service.getSummary(id);  // { status, stock, total }
```

→ N回呼び出しが1回になり、トランザクション境界も明確。

### 3. Builder / Fluent は控えめに

```ts
// 過剰
new QueryBuilder().select("*").from("users").where("id", 1).limit(1).execute()

// シンプル
repo.findById(1)
```

Builderは「組み合わせが本当に多様」なケースでのみ。

## TDD で陥りがちなInterface 劣化

### 1. Triangulation で引数が増える

新しいテストを通すために引数を追加 → 5個目を追加するときに **Value Object に集約**するRefactor を入れる。

### 2. 「とりあえず public」

「テストから呼びたい」だけで public にしない。**振る舞いベースのテスト**で対応。

### 3. Mock の引数が増える

Mock を書くのが辛い = Interface が悪いサイン:

```ts
// Mock が複雑 = Interface が悪い
const mockX = {
  foo: jest.fn(), bar: jest.fn(), baz: jest.fn(),
  qux: jest.fn(), ...
};
```

→ X を分割するか、Adapterを挟む。

## 関連

- `~/.claude/rules/architecture-language.md`: Module/Interface/Depth用語
- `improving-architecture` スキル: Interface改善の体系手順
- `design-an-interface` スキル: 並列で複数案を生成
