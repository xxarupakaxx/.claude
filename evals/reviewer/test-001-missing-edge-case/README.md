# test-001-missing-edge-case

## カテゴリ
test

## 対象 reviewer
test-reviewer

## 期待される検出

| ID | 重要度 | 該当行 | 内容 | 必須/任意 |
|----|-------|-------|------|---------|
| F1 | IMPORTANT | 14-30 | 境界値（0, 負, 空文字列, 小数）のテスト欠落 | must_detect |
| F2 | IMPORTANT | 14-30 | 異常系（throw 検証）のテスト欠落 | must_detect |
| F3 | MINOR | 14-30 | MAX_SAFE_INTEGER オーバーフローテスト | may_detect |
| F4 | MINOR | 14-30 | 全角数字 / non-ASCII 入力テスト | may_detect |

## ケース由来
- ハッピーパスのみのテストはコードカバレッジが高くてもバグを見逃す代表例
- test-reviewer は「網羅性」「エッジケース」を見落とさないことを評価
