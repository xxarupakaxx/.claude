# arch-001-shotgun-surgery

## カテゴリ
arch

## 対象 reviewer
arch-reviewer

## 期待される検出

| ID | 重要度 | 該当行 | 内容 | 必須/任意 |
|----|-------|-------|------|---------|
| F1 | IMPORTANT | 4-42 | 税率10% (1.10) が4ファイルに重複 (Shotgun Surgery) | must_detect |
| F2 | IMPORTANT | 4-42 | 価格計算ロジックの責務分離不足・凝集度低い | must_detect |
| F3 | MINOR | 4-42 | Money / Value Object 化の提案 | may_detect |

## ケース由来
- Fowler "Refactoring 2nd Ed" の Shotgun Surgery 例から派生
- 共通モジュール化されていないマジックナンバーが複数ファイルに散在するパターン

## 観点
税率変更時に4箇所修正が必要 → Locality 低 → アーキテクチャの設計問題。
arch-reviewer は「変更影響範囲の見積もり」を行うべきケース。
