// 投稿一覧API: 各 user について posts を1件ずつ取得（古典的 N+1）
import { db } from "./db";

export async function listUsersWithPostCounts() {
  // 1 クエリでユーザー全件取得
  const users = await db("users").select("id", "email");

  // ユーザーごとに posts.count を取得（N クエリ発生）
  const result = [];
  for (const u of users) {
    const posts = await db("posts").where("user_id", u.id).count<{ count: string }>("* as count");
    result.push({
      id: u.id,
      email: u.email,
      post_count: Number(posts[0].count),
    });
  }

  return result;
}

export async function listOrders() {
  const orders = await db("orders").select("id", "user_id", "total");

  // 各 order について user を 1 件ずつ取得（さらに N+1）
  const enriched = [];
  for (const o of orders) {
    const user = await db("users").where("id", o.user_id).first();
    enriched.push({ ...o, user });
  }

  return enriched;
}
