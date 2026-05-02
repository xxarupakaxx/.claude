// 価格計算ロジックが複数モジュールに散在（Shotgun Surgery のアンチパターン）

// ---- src/api/order.ts ----
export function createOrder(items: { id: string; price: number; qty: number }[]) {
  let total = 0;
  for (const item of items) {
    // 税率10%を加算（直書き）
    total += item.price * item.qty * 1.10;
  }
  return { total };
}

// ---- src/api/cart.ts ----
export function previewCart(items: { id: string; price: number; qty: number }[]) {
  let subtotal = 0;
  for (const item of items) {
    // 税率10%を加算（重複ロジック）
    subtotal += item.price * item.qty * 1.10;
  }
  return { subtotal };
}

// ---- src/email/receipt.ts ----
export function buildReceipt(items: { name: string; price: number; qty: number }[]) {
  const lines = items.map((i) => {
    // 税率10%を加算（さらに重複）
    const lineTotal = i.price * i.qty * 1.10;
    return `${i.name}: ¥${lineTotal}`;
  });
  return lines.join("\n");
}

// ---- src/admin/report.ts ----
export function totalSales(orders: { items: { price: number; qty: number }[] }[]) {
  let sum = 0;
  for (const o of orders) {
    for (const item of o.items) {
      // 税率10%を加算（4箇所目）
      sum += item.price * item.qty * 1.10;
    }
  }
  return sum;
}
