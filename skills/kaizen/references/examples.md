# コード例リファレンス

## 継続的改善

### 反復的な洗練の例（Good）

各ステップは完成しており、テスト済みで、正しく動作している。

```typescript
// 反復1：まず動かす
const calculateTotal = (items: Item[]) => {
  let total = 0;
  for (let i = 0; i < items.length; i++) {
    total += items[i].price * items[i].quantity;
  }
  return total;
};

// 反復2：分かりやすくする（リファクタリング）
const calculateTotal = (items: Item[]): number => {
  return items.reduce((total, item) => {
    return total + (item.price * item.quantity);
  }, 0);
};

// 反復3：堅牢にする（バリデーション追加）
const calculateTotal = (items: Item[]): number => {
  if (!items?.length) return 0;

  return items.reduce((total, item) => {
    if (item.price < 0 || item.quantity < 0) {
      throw new Error('価格と数量は0以上でなければならない');
    }
    return total + (item.price * item.quantity);
  }, 0);
};
```

### すべてを一度にやろうとする例（Bad）

圧倒的で、エラーを生みやすく、検証が困難。

```typescript
// すべてを一度にやろうとしている例
const calculateTotal = (items: Item[]): number => {
  // バリデーション、最適化、機能追加、エッジケース対応をすべて同時に実装
  if (!items?.length) return 0;
  const validItems = items.filter(item => {
    if (item.price < 0) throw new Error('価格が負の値です');
    if (item.quantity < 0) throw new Error('数量が負の値です');
    return item.quantity > 0; // 数量0も除外
  });
  // さらにキャッシュ、ログ、通貨変換なども追加…
  return validItems.reduce(...); // 責務が多すぎる
};
```

---

## ポカヨケ

### 型システムによるエラー防止

#### 判別共用体で不正な状態を表現不可能にする（Good）

型システムがエラーのクラス全体を防ぐ。

```typescript
// 悪い例：status が任意の文字列を取れる
type OrderBad = {
  status: string; // "pending", "PENDING", "pnding" など何でも入る
  total: number;
};

// 良い例：有効な状態のみ許可
type OrderStatus = 'pending' | 'processing' | 'shipped' | 'delivered';
type Order = {
  status: OrderStatus;
  total: number;
};

// さらに良い例：状態ごとに関連データを持つ
type Order =
  | { status: 'pending'; createdAt: Date }
  | { status: 'processing'; startedAt: Date; estimatedCompletion: Date }
  | { status: 'shipped'; trackingNumber: string; shippedAt: Date }
  | { status: 'delivered'; deliveredAt: Date; signature: string };

// trackingNumberなしで shipped になることは不可能
```

#### NonEmptyArray で空配列を型レベルで防止する（Good）

関数シグネチャが安全性を保証する。

```typescript
// 不正な状態を表現できないようにする
type NonEmptyArray<T> = [T, ...T[]];

const firstItem = <T>(items: NonEmptyArray<T>): T => {
  return items[0]; // 常に安全、undefined にならない
};

// 呼び出し側は配列が空でないことを保証する必要がある
const items: number[] = [1, 2, 3];
if (items.length > 0) {
  firstItem(items as NonEmptyArray<number>); // 安全
}
```

### バリデーションによるエラー防止

#### 境界で一度だけ検証し、branded type で安全に使う（Good）

境界で一度だけ検証し、それ以降は安全に使う。

```typescript
// 悪い例：使用後にバリデーション
const processPayment = (amount: number) => {
  const fee = amount * 0.03; // バリデーション前に使用している
  if (amount <= 0) throw new Error('不正な金額');
};

// 良い例：即時バリデーション
const processPayment = (amount: number) => {
  if (amount <= 0) {
    throw new Error('支払金額は正の値でなければならない');
  }
  if (amount > 10000) {
    throw new Error('支払金額が上限を超えています');
  }

  const fee = amount * 0.03;
};

// さらに良い例：境界で branded type による検証
type PositiveNumber = number & { readonly __brand: 'PositiveNumber' };

const validatePositive = (n: number): PositiveNumber => {
  if (n <= 0) throw new Error('正の値でなければならない');
  return n as PositiveNumber;
};

const processPayment = (amount: PositiveNumber) => {
  const fee = amount * 0.03;
};

// システム境界で一度だけ検証
const handlePaymentRequest = (req: Request) => {
  const amount = validatePositive(req.body.amount);
  processPayment(amount);
};
```

### ガードと事前条件

#### 早期リターンでネストを防ぎ、前提条件を明示する（Good）

ガードにより前提条件が明示され、強制される。

```typescript
// 早期リターンでネストを防ぐ
const processUser = (user: User | null) => {
  if (!user) {
    logger.error('ユーザーが見つかりません');
    return;
  }

  if (!user.email) {
    logger.error('メールアドレスがありません');
    return;
  }

  if (!user.isActive) {
    logger.info('ユーザーは無効です。スキップします');
    return;
  }

  // ここでは user が有効でアクティブであることが保証される
  sendEmail(user.email, 'ようこそ！');
};
```

### 設定のエラー防止

#### 必須設定を型で強制し、起動時に失敗させる（Good）

本番ではなく起動時に失敗させる。

```typescript
// 悪い例：オプション設定と危険なデフォルト
type ConfigBad = {
  apiKey?: string;
  timeout?: number;
};

const client = new APIClient({ timeout: 5000 }); // apiKey がない

// 良い例：必須設定、早期失敗
type Config = {
  apiKey: string;
  timeout: number;
};

const loadConfig = (): Config => {
  const apiKey = process.env.API_KEY;
  if (!apiKey) {
    throw new Error('API_KEY 環境変数が必要です');
  }

  return {
    apiKey,
    timeout: 5000,
  };
};

const config = loadConfig();
const client = new APIClient(config);
```
