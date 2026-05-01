# Deep Modules in TDD

> Deep Module: 小さな Interface ＋ 厚い Implementation。利用者の認知負荷を下げる。

詳細な定義: `~/.claude/rules/architecture-language.md`

## TDD と Deep Module の関係

TDD は **Interface 設計のドライバ** になる。
テストを書く＝**呼び出し側の体験を先に作る**ため、Interface が自然と「使いやすい形」に収束する。

ただし放置すると **Shallow に流れる**:
- Triangulation でデータを増やすたびに引数も増える
- 「テストしやすさ」のために getter/setter を露出
- 内部状態を assert したくて public にする

これらを防ぐ意識が必要。

## Deep を促す書き方

### 1. テストは公開Interfaceのみ呼ぶ

```ts
// Bad: 内部状態にアクセス
const cart = new Cart();
cart._items.push(item);  // private にしたい
expect(cart._total).toBe(100);  // computeTotal() を呼ぶべき

// Good: 公開Interface経由
const cart = new Cart();
cart.add(item);
expect(cart.total).toBe(100);
```

→ private を private のまま保てる = Deep維持。

### 2. 結果を観測する手段を Interface に含める

「testabilityのために」ではなく「**利用者にも有益**」という形で公開する:

```ts
// Bad: テスト用のフラグ
class TaxCalculator {
  calculate(amount: number, _testMode?: boolean) { ... }
}

// Good: 結果に内訳情報を含める（実利用にも有益）
class TaxCalculator {
  calculate(amount: number): { total: number; breakdown: TaxBreakdown }
}
```

### 3. パラメータを増やすのではなく Value Object に集約

```ts
// Shallow: パラメータが肥大化
service.createOrder(userId, items, couponCode, billingAddress, shippingAddress, ...)

// Deep: 1つの意味のある型
service.createOrder(orderRequest)
```

`orderRequest` の組み立て側にロジックが集約される＝Information Hiding が進む。

### 4. Hard-coded Constants をInterfaceに出さない

```ts
// Bad: 利用者にretry回数を強要
client.fetch(url, retries: 3)

// Good: 賢いデフォルトをモジュール内で隠蔽
client.fetch(url)  // 内部で retries=3
```

利用者から見える表面積を減らす = Deep。

## Refactor フェーズで Deep を強化する

各サイクルの Refactor で次を確認:

### チェックリスト

- [ ] 公開メソッド数は増えていないか？（増えたらまとめられないか検討）
- [ ] 引数の数が3を超えていないか？（Value Object へ集約）
- [ ] private にできる public はないか？（テストは公開Interfaceから）
- [ ] 利用者が `if/else` で内部状態を分岐していないか？（メソッドへ吸い上げ）
- [ ] 同じ前提知識を複数モジュールが持っていないか？（Information Leakage）

## アンチパターン

### Premature Generalization

「将来の拡張」を見越して引数を増やす:

```ts
// Bad
processOrder(order, options: { retry?: number; timeout?: number; trace?: boolean; ... })
```

YAGNI 違反。**テストが要求した分だけ** Interfaceを広げる。

### Pass-through Wrapper

```ts
// Shallow: 何も足していない
class UserRepository {
  findById(id: string) { return this.db.users.findOne({ id }); }
}
```

`db.users.findOne` を直接呼べばよい。
**Repository を作るなら** transaction 管理、cache、N+1 対策などを **追加** すること（Pull Complexity Downward）。

### Test-induced Leakage

テストのために getter を公開→実装変更でテスト破綻:

```ts
class Cart {
  get _internalState() { return this.state; }  // テスト用に公開
}
```

→ Refactor で state を分割した瞬間に全テスト破綻。
**振る舞いをテスト**する設計に戻す。

## 判定: あなたのモジュールは Deep か？

| 指標 | Shallow | Deep |
|------|--------|------|
| public メソッド数 | 多い (>10) | 少ない (<5) |
| 平均引数数 | 多い (>3) | 少ない (≤2) |
| 利用者の前提知識量 | 多い | 少ない |
| Information Hiding | 弱い | 強い |
| Implementation/Interface 比 | <2 | >5 |

Refactor フェーズで上記を点検。
