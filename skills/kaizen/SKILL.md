---
name: kaizen
description: コードの実装およびリファクタリング、システムのアーキテクチャ設計・設計作業、プロセスおよびワークフローの改善、エラーハンドリングとバリデーションを行う際に使用する。過剰設計を避け、反復的な改善を適用するための技法を提供する。
model: opus
---

# カイゼン：継続的改善

継続的改善のマインドセットを適用する。小さな反復的改善、エラーを防ぐ設計、確立されたパターンの遵守、過剰設計の回避を提案し、品質とシンプルさを導くために自動的に適用される。

## 概要

小さな改善を、継続的に。設計によってエラーを防ぐ。うまくいく方法に従う。本当に必要なものだけを作る。

**中核原則:** 一度の大きな変更よりも、多くの小さな改善の方が効果的である。修正によってではなく、設計段階でエラーを防ぐ。

## 使用する場面

**常に適用される対象:**

- コードの実装およびリファクタリング  
- アーキテクチャおよび設計上の意思決定  
- プロセスおよびワークフローの改善  
- エラーハンドリングおよびバリデーション  

**哲学:** 大規模な努力による完璧さではなく、段階的な進歩と予防による品質。

## 4つの柱

### 1. 継続的改善（Kaizen）

小さく頻繁な改善は、大きな成果へと積み重なる。

#### 原則

**革命的よりも漸進的に:**

- 品質を向上させる最小限の変更を行う  
- 一度に1つの改善  
- 各変更を検証してから次へ進む  
- 小さな成功を積み重ねて勢いを作る  

**常にコードをより良くして終える:**

- 出会った小さな問題を修正する  
- 作業の範囲内でリファクタリングする  
- 古くなったコメントを更新する  
- 不要なコードを見つけたら削除する  

**反復的な洗練:**

- 最初の版：動くようにする  
- 2回目：分かりやすくする  
- 3回目：効率的にする  
- 一度にすべてをやろうとしない  

<Good>
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
````

各ステップは完成しており、テスト済みで、正しく動作している </Good>

<Bad>
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

圧倒的で、エラーを生みやすく、検証が困難 </Bad>

#### 実務での適用

**機能を実装するとき:**

1. 動く最もシンプルなバージョンから始める
2. 改善を1つ追加する（エラーハンドリング、バリデーションなど）
3. テストして検証する
4. 時間が許せば繰り返す
5. 最初から完璧を目指さない

**リファクタリング時:**

* 一度に1つのコードスメルを修正する
* 改善ごとにコミットする
* 常にテストを通した状態を保つ
* 「十分良い」時点で止める（限界効用の低下）

**コードレビュー時:**

* 書き直しではなく段階的な改善を提案する
* 優先順位：致命的 → 重要 → あれば良い
* 最も影響が大きい変更から着手する
* 完璧でなくても「以前より良い」ことを受け入れる

---

### 2. ポカヨケ（エラー防止）

実行時ではなく、設計時・コンパイル時にエラーを防ぐシステムを設計する。

#### 原則

**エラーを不可能にする:**

* 型システムがミスを検出する
* コンパイラが契約を強制する
* 不正な状態を表現できない
* 早期にエラーを検出する（本番より前）

**安全のための設計:**

* 早く、はっきり失敗する
* 分かりやすいエラーメッセージを提供する
* 正しい道を明確にする
* 間違った道を難しくする

**多層防御:**

1. 型システム（コンパイル時）
2. バリデーション（ランタイム初期）
3. ガード（事前条件）
4. エラーバウンダリ（段階的劣化処理）

#### 型システムによるエラー防止

<Good>
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

````

型システムがエラーのクラス全体を防ぐ  
</Good>

<Good>
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
````

関数シグネチャが安全性を保証する </Good>

#### バリデーションによるエラー防止

<Good>
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

````

境界で一度だけ検証し、それ以降は安全に使う  
</Good>

#### ガードと事前条件

<Good>
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
````

ガードにより前提条件が明示され、強制される </Good>

#### 設定のエラー防止

<Good>
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

本番ではなく起動時に失敗させる  
</Good>

---

### 3. 標準化された作業

確立されたパターンに従い、うまくいく方法を文書化し、良い実践を簡単に守れるようにする。

#### 原則

**賢さより一貫性:**

- 既存コードベースのパターンに従う  
- 解決済み問題を再発明しない  
- 明確に優れている場合のみ新パターンを導入  
- 新パターンはチームで合意する  

**ドキュメントはコードと共に:**

- README：セットアップとアーキテクチャ  
- CLAUDE.md：AIコーディング規約  
- コメントは「何を」ではなく「なぜ」を書く  
- 複雑なパターンには例を示す  

**標準を自動化:**

- Linter によるスタイル強制  
- 型チェックによる契約強制  
- テストによる動作検証  
- CI/CD による品質ゲート  

---

### 4. ジャストインタイム（JIT）

今必要なものだけを作る。それ以上でも以下でもない。早すぎる最適化や過剰設計を避ける。

#### 原則

**YAGNI（どうせ必要にならない）:**

- 現在の要件のみ実装する  
- 「念のため」の機能は作らない  
- 「将来必要かも」というコードは書かない  
- 推測による実装は削除する  

**動く最も単純なもの:**

- まずは素直な解決策から始める  
- 必要になったら複雑さを追加する  
- 要件が変わったらリファクタリングする  
- 将来を先読みしすぎない  

**測定してから最適化する:**

- 早すぎる最適化は禁止  
- 最適化の前にプロファイルする  
- 変更の影響を測定する  
- 「十分速い」性能を受け入れる  

---

## 覚えておくこと

**Kaizen とは:**

- 小さな改善を継続すること  
- 設計によってエラーを防ぐこと  
- 実証済みのパターンに従うこと  
- 必要なものだけを作ること  

**Kaizen ではないもの:**

- 最初から完璧を目指すこと  
- 大規模なリファクタリング  
- 賢すぎる抽象化  
- 早すぎる最適化  

**マインドセット:**  
今日は十分に良く、明日はもっと良く。これを繰り返す。
