# perf-001-n-plus-one

## カテゴリ
perf

## 対象 reviewer
perf-reviewer

## 期待される検出

| ID | 重要度 | 該当行 | 内容 | 必須/任意 |
|----|-------|-------|------|---------|
| F1 | CRITICAL | 9-17 | listUsersWithPostCounts: ユーザーごとに posts.count を個別クエリ (N+1) | must_detect |
| F2 | CRITICAL | 25-30 | listOrders: order ごとに user を個別取得 (N+1) | must_detect |
| F3 | MINOR | 4-32 | user_id インデックス確認の提案 | may_detect |

## ケース由来
- N+1 クエリは web framework 全般で頻発する代表的パフォーマンス問題
- knex 環境では `whereIn` / `groupBy` を使った一括取得で解決可能

## 観点
perf-reviewer は「ループ内 await」「クエリループ」を見落とさないことを評価。
