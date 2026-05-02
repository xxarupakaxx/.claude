# cq-001-magic-numbers

## カテゴリ
code-quality

## 対象 reviewer
code-quality-reviewer

## 期待される検出

| ID | 重要度 | 該当行 | 内容 | 必須/任意 |
|----|-------|-------|------|---------|
| F1 | IMPORTANT | 7-22 | マジックナンバー（100/1000000/50000/500）の定数化欠如 | must_detect |
| F2 | IMPORTANT | 33-45 | process/processRefund の検証ロジック重複（Rule of Three 該当） | must_detect |
| F3 | MINOR | 22-26 | 1文字変数 `x` の命名改善 | may_detect |

## ケース由来
- 業務系コードで頻発するコード品質課題の代表例
- code-quality-reviewer は「マジックナンバー検出」「重複検出」「命名」を見落とさないことを評価
