# Library Research Rules

ライブラリ/フレームワーク使用時に適用されるルール。

## Context7を使う場面

- 新しいライブラリの導入検討・API確認
- バージョンアップ時の変更点確認
- エラー解決時の公式ドキュメント参照

## 使用手順

1. `resolve-library-id`でライブラリIDを取得
2. `query-docs`でドキュメントを取得

## ツールの使い分け

| 目的 | ツール |
|------|--------|
| ライブラリの最新API確認 | **Context7** |
| OSSリポジトリの設計理解 | **deepwiki** |
| 一般的な技術情報 | **WebSearch** |

## メジャーバージョンアップ時（IMPORTANT）

3ツールを**必ず全て使用**:
1. **Context7**: migration guide, breaking changes, 新API仕様
2. **deepwiki**: 構造変更、サンプルコード
3. **WebSearch/GitHub Issues**: 既知の問題、コミュニティの解決策

移行手順の詳細は workflow-rules.md Phase 1.3 を参照。

## 注意事項

- Context7が対応していない場合はdeepwikiまたはWebSearch使用
- ライブラリIDが不明な場合は`resolve-library-id`で検索
