# Refactor Phase: 緑のまま改善する

## 大原則

### 1. テストを変更しない

Refactor フェーズで **テストを変えるのは禁止**:
- テストを変える＝振る舞いの変更
- それは新しい Red→Green サイクル

例外: テスト自身のリファクタ（重複ヘルパー抽出等）。これも独立したコミットにする。

### 2. 緑→緑を維持

各小さな変更ごとにテスト実行:
- 1分以内に1テストサイクル
- 落ちたら直前の変更を **巻き戻す**（探求しない）
- git の細かいコミットで安全網を張る

### 3. 1Refactor = 1論点

- 「重複削除」と「命名改善」を同じ commit にしない
- スコープを絞ることで「何が壊したか」を1秒で特定可能に

## Refactor の優先順位

優先度の高い改善から行う:

### 1. テストの匂い（Test Smells）の除去

- Setup の重複 → ヘルパー関数 / Factory
- assert の重複 → カスタム matcher
- 命名の不一致 → リネーム

### 2. Duplication の除去（Rule of Three）

```
1回目: そのまま書く
2回目: 重複を許容
3回目: 抽象化を検討
```

早すぎる抽象化（Rule of Three 未達）は逆効果。

### 3. Naming

意図を表す名前へ:

```ts
// Bad
function calc(x: number) { return x * 0.1; }

// Good
function calculateConsumptionTax(amount: number) { return amount * 0.1; }
```

魔法の数値は名前付き定数へ:

```ts
// Bad
if (user.failedAttempts > 5) { lock(); }

// Good
const MAX_LOGIN_ATTEMPTS = 5;
if (user.failedAttempts > MAX_LOGIN_ATTEMPTS) { lock(); }
```

### 4. Function Size

80行を超えたら分割を検討:
- 抽出する関数は **意味のある単位**（行数で機械的に切らない）
- 関数名で「何をするか」を表現できるかが分割の目安

### 5. Deep Module への昇華

`references/deep-modules.md` のチェックリストで点検:
- public/private の境界を見直す
- 引数を Value Object に集約
- 利用者の認知負荷を下げる

### 6. Seam の整理

System Boundary が直叩きされていないか確認:
- `Date.now()` → Clock 経由
- `process.env.X` → Config 経由
- `fetch(...)` → HttpClient 経由

## Refactor のテクニック

### Extract Function

```ts
// Before
function processOrder(order) {
  // 30行の在庫チェック
  // 30行の支払い処理
  // 30行の通知送信
}

// After
function processOrder(order) {
  reserveStock(order);
  charge(order);
  notify(order);
}
```

### Inline Variable

```ts
// Before
const isOver18 = user.age >= 18;
if (isOver18) { ... }

// After (一度しか使わないなら)
if (user.age >= 18) { ... }
```

### Replace Conditional with Polymorphism

```ts
// Before
function calculate(type, amount) {
  if (type === "percent") return amount * 0.1;
  if (type === "flat") return 100;
  if (type === "tiered") return amount > 1000 ? 200 : 100;
}

// After
interface Pricing { calculate(amount: number): number }
class PercentPricing implements Pricing { ... }
class FlatPricing implements Pricing { ... }
class TieredPricing implements Pricing { ... }
```

ただし **3パターン以上**で初めて適用。2つなら `if/else` のままで良い。

### Move Method

データを多く参照しているクラスへメソッドを移動:

```ts
// Before
class Order {
  calculateTax(taxRate: TaxRate) {
    return this.items.reduce((sum, i) => sum + i.price * taxRate.rate, 0);
  }
}

// After (taxRate のロジックなのでTaxRate側へ)
class TaxRate {
  applyTo(items: OrderItem[]) {
    return items.reduce((sum, i) => sum + i.price * this.rate, 0);
  }
}
```

## やってはいけない Refactor

### 1. 振る舞いの変更

「ついでに」エラーメッセージを変えるな。テスト変更が必要なら別サイクル。

### 2. テスト未追加領域への踏み込み

カバーされていない分岐を Refactor すると **検出されない壊れ方** をする。
先にテストを追加（characterization test）してから Refactor。

### 3. 「全部きれいに」しようとする

Refactor は **痛みのある所** だけ。読めて変更しやすければ十分。

### 4. 設計パターンの押し付け

「Strategyパターンを使いたい」が先に立つ＝アンチパターン。
**問題が先、パターンは後**。

## 完了判定

Refactor フェーズを終わるタイミング:

- [ ] テストが全て緑
- [ ] 1つの改善目的が達成された
- [ ] これ以上の Refactor は次サイクル以降で十分

→ commit して次のRedへ。

## 関連

- `improving-architecture` スキル: 大規模Refactorの体系手順
- `~/.claude/rules/common-patterns.md`: 推奨パターン/アンチパターン
