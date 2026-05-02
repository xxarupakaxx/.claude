// 注文処理ロジック (TypeScript)
// マジックナンバー / 命名 / 重複ロジックのコード品質問題が混在

export class OrderProcessor {
  process(order: { items: { price: number; qty: number }[]; userId: string }) {
    // 注文金額の最低制限チェック（マジックナンバー 100）
    const sum = order.items.reduce((a, i) => a + i.price * i.qty, 0);
    if (sum < 100) {
      throw new Error("Order too small");
    }

    // 上限チェック（マジックナンバー 1000000）
    if (sum > 1000000) {
      throw new Error("Order too large");
    }

    // VIP判定（マジックナンバー、なぜ50000?）
    const isVip = sum > 50000;

    // 配送料計算（同じ閾値が再登場）
    const shipping = sum > 50000 ? 0 : 500;

    // 1文字変数 a, i, x が多用される
    const x = sum + shipping;

    return {
      userId: order.userId,
      total: x,
      vip: isVip,
    };
  }

  // ほぼ同じロジックがリファンド側にも重複
  processRefund(order: { items: { price: number; qty: number }[]; userId: string }) {
    const sum = order.items.reduce((a, i) => a + i.price * i.qty, 0);
    if (sum < 100) {
      throw new Error("Refund too small");
    }
    if (sum > 1000000) {
      throw new Error("Refund too large");
    }
    return {
      userId: order.userId,
      total: -sum,
    };
  }
}
