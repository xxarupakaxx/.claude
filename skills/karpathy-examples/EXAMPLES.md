# Karpathy 4原則: Before/After 実例集（TypeScript版）

LLMがやりがちな失敗と、原則に従った修正例。4原則ごとに特に価値が高い1例ずつをTypeScriptで示す（計4例）。アンチパターン早見表を末尾に併置。

---

## 1. Think Before Coding: Hidden Assumptions（隠れた仮定）

**ユーザー依頼**: 「ユーザーデータをエクスポートする機能を追加して」

### ❌ LLMがやりがちな失敗（仮定を勝手に置く）

```ts
async function exportUsers(format: 'json' | 'csv' = 'json'): Promise<string> {
  const users = await User.findAll();

  if (format === 'json') {
    await fs.writeFile('users.json', JSON.stringify(users.map(u => u.toJSON())));
  } else {
    const rows = users.map(u => `${u.id},${u.email},${u.name}`);
    await fs.writeFile('users.csv', ['id,email,name', ...rows].join('\n'));
  }

  return `Exported ${users.length} users`;
}
```

**問題点**:
- 全ユーザーをエクスポートしてよいと仮定（プライバシー懸念は？ページネーションは？）
- ファイル出力先を勝手に決定（ブラウザDL？バックグラウンドジョブ？APIレスポンス？）
- 含めるフィールドを勝手に選定（センシティブ情報があるかも）
- CSV のフィールド名を実データ構造の確認なく決定

### ✅ 正しい振る舞い（仮定を表に出す）

```
実装前にいくつか確認させてください:

1. **スコープ**: 全ユーザー対象？フィルタ付き？（プライバシー影響）
2. **形式**: 「エクスポート」とは:
   - ブラウザ上でファイルDL？
   - バックグラウンドジョブ + メール通知？
   - JSON を返す API エンドポイント？
3. **フィールド**: どのフィールドを含めるか（センシティブ情報除外要否）
4. **ボリューム**: 通常何件規模か（実装方針に影響）

最小実装案: ページネーション付き JSON を返す API エンドポイント。
ファイルベースのエクスポートが必要なら追加情報を確認させてください。

どれが希望ですか？
```

---

## 2. Simplicity First: Over-abstraction（過度な抽象化）

**ユーザー依頼**: 「割引額を計算する関数を追加して」

### ❌ LLMがやりがちな失敗（過剰設計）

```ts
interface DiscountStrategy {
  calculate(amount: number): number;
}

class PercentageDiscount implements DiscountStrategy {
  constructor(private percentage: number) {}
  calculate(amount: number): number {
    return amount * (this.percentage / 100);
  }
}

class FixedDiscount implements DiscountStrategy {
  constructor(private fixedAmount: number) {}
  calculate(amount: number): number {
    return Math.min(this.fixedAmount, amount);
  }
}

interface DiscountConfig {
  strategy: DiscountStrategy;
  minPurchase?: number;
  maxDiscount?: number;
}

class DiscountCalculator {
  constructor(private config: DiscountConfig) {}

  applyDiscount(amount: number): number {
    const { minPurchase = 0, maxDiscount = Infinity, strategy } = this.config;
    if (amount < minPurchase) return 0;
    return Math.min(strategy.calculate(amount), maxDiscount);
  }
}

// 単純な計算のために 30 行以上のセットアップが必要
```

### ✅ 正しい振る舞い（シンプル）

```ts
function calculateDiscount(amount: number, percent: number): number {
  return amount * (percent / 100);
}

// 使用
const discount = calculateDiscount(100, 10);  // 10
```

**複雑性を追加する条件**: 実際に複数の割引種別が必要になったとき。その要件が来てからリファクタする。

---

## 3. Surgical Changes: Drive-by Refactoring（依頼外の改善）

**ユーザー依頼**: 「空のメールアドレスでバリデータがクラッシュするバグを直して」

### ❌ LLMがやりがちな失敗（ついでに色々改善）

```diff
- export function validateUser(userData: UserData): boolean {
+ /**
+  * Validate user data.
+  * @throws {ValidationError} if any field is invalid
+  */
+ export function validateUser(userData: UserData): boolean {
+   // Validate email
-   if (!userData.email) {
+   const email = userData.email?.trim() ?? '';
+   if (!email) {
      throw new Error('Email required');
    }
-   if (!userData.email.includes('@')) {
+   if (!email.includes('@') || !email.split('@')[1].includes('.')) {
      throw new Error('Invalid email');
    }
-   if (!userData.username) {
+   // Validate username
+   const username = userData.username?.trim() ?? '';
+   if (!username) {
      throw new Error('Username required');
    }
+   if (username.length < 3) {
+     throw new Error('Username too short');
+   }
+   if (!/^[a-zA-Z0-9]+$/.test(username)) {
+     throw new Error('Username must be alphanumeric');
+   }
    return true;
  }
```

**問題点**:
- バグ修正の範囲を超えてメールバリデーション強化
- 頼まれてないユーザー名バリデーション追加
- コメント変更
- docstring 追加

### ✅ 正しい振る舞い（外科的）

```diff
  export function validateUser(userData: UserData): boolean {
-   if (!userData.email) {
+   const email = userData.email ?? '';
+   if (!email || !email.trim()) {
      throw new Error('Email required');
    }
    if (!userData.email.includes('@')) {
      throw new Error('Invalid email');
    }
    if (!userData.username) {
      throw new Error('Username required');
    }
    return true;
  }
```

**変更したのは**: 空メールハンドリングを直す行のみ。他は触らない。

---

## 4. Goal-Driven Execution: Test-First Verification（テスト先行検証）

**ユーザー依頼**: 「スコアが重複するときソートが壊れる」

### ❌ LLMがやりがちな失敗（再現せずに直す）

```ts
// 即座にソートロジックを変更（バグを再現確認していない）
export function sortScores(scores: Score[]): Score[] {
  return [...scores].sort((a, b) => b.score - a.score || a.name.localeCompare(b.name));
}
```

### ✅ 正しい振る舞い（先に再現テスト）

```ts
// 1. まず再現テストを書く
import { describe, it, expect } from 'vitest';
import { sortScores } from './sort-scores';

describe('sortScores with duplicate scores', () => {
  it('should produce deterministic order for ties', () => {
    const scores = [
      { name: 'Alice', score: 100 },
      { name: 'Bob', score: 100 },
      { name: 'Charlie', score: 90 },
    ];

    // 同じ入力に対して同じ結果が返ることを期待
    const result1 = sortScores(scores);
    const result2 = sortScores(scores);
    expect(result1).toEqual(result2);

    // tie-breaker は名前昇順を期待
    expect(result1[0].name).toBe('Alice');
    expect(result1[1].name).toBe('Bob');
  });
});

// → このテストを 10 回実行 → 順序が非決定的で失敗することを確認

// 2. 修正
export function sortScores(scores: Score[]): Score[] {
  return [...scores].sort((a, b) => b.score - a.score || a.name.localeCompare(b.name));
}

// 3. テスト再実行 → 安定的にパス
```

---

## アンチパターン早見表

| 原則 | アンチパターン | 修正方針 |
|------|----------------|----------|
| Think Before Coding | フィールド/スコープ/形式を黙って決める | 仮定を列挙し、明示確認 |
| Simplicity First | 1 種類の割引のために Strategy パターンを導入 | 必要になるまで 1 関数で済ます |
| Simplicity First | `save` 関数に `merge/validate/notify` フラグを先回り追加 | 要求が出てから足す（Speculative Features 違反） |
| Surgical Changes | バグ修正のついでに quote/type hint/docstring 変更 | 報告された問題の行だけ修正（Style Drift 防止） |
| Surgical Changes | 関連する未変更コードを「綺麗にする」 | 触らない。気づいた場合は別途指摘 |
| Goal-Driven | 「レビューして改善する」と曖昧に進める | 「バグX再現テスト → 通す → リグレッション無確認」と分解 |
| Goal-Driven | 全機能を一度にコミット | 各ステップに verify 基準を設けて段階デプロイ |

## 補足アンチパターン（1行サマリー）

主要4例の他にもよく見られるパターン:

- **Multiple Interpretations**（Think Before Coding）: 「速くして」が「レスポンス時間」「スループット」「体感速度」のどれか黙って選ばない
- **Speculative Features**（Simplicity First）: 「設定保存」に caching/notification/validation を先回り実装しない
- **Style Drift**（Surgical Changes）: 既存ファイルのクォート種別・type hint 有無に合わせる
- **Vague vs Verifiable**（Goal-Driven Execution）: 「認証を直す」を「セッション無効化テスト → 実装 → 既存テスト緑」へ分解

## 主要な洞察

「過剰設計」例は明らかに間違いではなく、デザインパターンやベストプラクティスに従っている。問題は**タイミング**。複雑性を必要になる前に追加すると:

- コードが理解しにくくなる
- バグが増える
- 実装に時間がかかる
- テストが難しい

「シンプル」版は理解しやすく、速く実装でき、テストしやすく、必要になった時点でリファクタできる。

**良いコードとは、明日の問題を先回りで解くのではなく、今日の問題をシンプルに解くコード。**
