# sec-001-sql-injection

## カテゴリ
security

## 対象 reviewer
security-reviewer

## 期待される検出

| ID | 重要度 | 該当行 | 内容 | 必須/任意 |
|----|-------|-------|------|---------|
| F1 | CRITICAL | 8-9 | LIKE 句で `${name}` を直接埋め込み | must_detect |
| F2 | CRITICAL | 17-18 | id を文字列連結で SQL に埋め込み | must_detect |
| F3 | IMPORTANT | 25-28 | DELETE エンドポイントで入力検証欠如 | may_detect |
| F4 | IMPORTANT | 25-28 | DELETE エンドポイントで認可チェック欠如 | may_detect |

## ケース由来
- OWASP Top 10 A03:2021 Injection の代表パターン
- Express + クエリパラメータ + db.raw の組み合わせは現実のバグで頻発
