---
name: caveman
description: "コード/文章/設計を「原始人モード」で極限までシンプルにする。ユーザーが明示的に呼び出した場合のみ使用。「caveman モードで」「もっとシンプルに」「原始人モードで書き直して」等の依頼に対応。"
disable-model-invocation: true
---

# Caveman Mode - 原始人モードで簡素化

> 賢く書こうとする本能を捨て、**最も愚直で最も短い**形へ書き直す。

このスキルは **明示的な呼び出し時のみ** 起動する（自動推論で勝手に起動しない）。

## 哲学

**Caveman 原則**:
1. 名前は短く具体的に
2. 抽象化は禁止（インターフェース・継承・パターン）
3. ロジックは1直線（早期return すらしない、if/else のみ）
4. コメントは「なぜ」のみ。「何を」のコメントは削除
5. ライブラリより組込み関数
6. 行数を減らすことが正義

## 適用範囲

呼び出し時にユーザーが指定した対象に限定:
- 1関数・1ファイル単位での書き直し
- 設計ドキュメントの圧縮
- README・コメントの簡素化

**広範囲（プロジェクト全体）には適用しない**。Caveman は局所的な薬。

## 手順

### 1. 元の意図を1文で抽出

「この関数は **何を** するか」を **1文** で書く（実装抜きで）。

### 2. 最小実装を書く

抽出した1文だけを満たす最小コードを書く:
- 直線的フロー
- 名前は3-7文字目安
- 引数は3個以内
- 戻り値は単一型

### 3. 削れるものを全部削る

以下を削除:
- ヘルパー関数（インライン化）
- 早期return（if/else に統一して見通しを優先）
- ログ・メトリクス（必要最小限以外）
- エラーハンドリング（System Boundary 以外）
- 型エイリアス（直接書く）
- コメント（「なぜ」だけ残す）

### 4. テストで担保を確認

書き直した結果、既存テストが通ることを確認。
通らなければ Caveman 失敗 → 元に戻す。

## 例

### Before（賢いコード）

```ts
interface OrderProcessor {
  process(order: Order): Result<Receipt, Error>;
}

class StandardOrderProcessor implements OrderProcessor {
  constructor(
    private readonly stockReserver: StockReserver,
    private readonly paymentGateway: PaymentGateway,
    private readonly notifier: Notifier,
  ) {}

  async process(order: Order): Promise<Result<Receipt, Error>> {
    // 在庫を確保する
    const stockResult = await this.stockReserver.reserve(order.items);
    if (stockResult.isErr()) return Err(stockResult.error);

    // 支払いを処理する
    const paymentResult = await this.paymentGateway.charge(order.payment);
    if (paymentResult.isErr()) {
      await this.stockReserver.release(order.items);
      return Err(paymentResult.error);
    }

    // 通知を送信する
    await this.notifier.notify(order.customer);

    return Ok(new Receipt(order, paymentResult.value));
  }
}
```

### After（Caveman）

```ts
async function processOrder(order: Order, deps: Deps): Promise<Receipt> {
  await deps.stock.reserve(order.items);
  try {
    const pay = await deps.pay.charge(order.payment);
    await deps.notify(order.customer);
    return { order, pay };
  } catch (e) {
    await deps.stock.release(order.items);
    throw e;
  }
}
```

**変化**:
- interface 削除（直接 function）
- class 削除（function + deps 引数）
- Result 型削除（throw に統一）
- コメント削除
- 行数: 25行 → 11行

## やってはいけない Caveman

### 1. 公開APIを破壊する Caveman

呼び出し側が多数あるコードでシグネチャを変えると **Shotgun Surgery** を誘発する。
影響範囲を必ず先に確認。

### 2. テスト不可能になる Caveman

依存を直接 `import` してハードコードしないこと（Seam を残す）。

### 3. 「読みやすさ」より「短さ」を優先しすぎる

- 1文字変数名は禁止（最低3文字）
- 三項演算子の3段ネストは可読性を破壊する → 禁止

## 完了基準

- [ ] 元のテストが全て通る
- [ ] 行数が元の50%以下、または読みやすさが明確に向上
- [ ] 削除したものを質問されても1分以内に説明できる

## 関連

- `improving-architecture` スキル: 大規模な構造改善（こちらは局所的）
- `zoom-out` スキル: 逆方向（鳥瞰）
