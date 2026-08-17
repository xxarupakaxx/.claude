# Notion DB スキーマ設計

## レコード単位

**1機能項目 = 1レコード**を推奨する（1マイルストーン=1レコードだと後から検索・フィルタしづらいため）。マイルストーン全体のサマリーが欲しい場合は、別途「マイルストーン」プロパティでグルーピングして見せる（DB内のグループ化ビューで対応。別テーブルは作らない）。

新規DB作成時は、この単位でよいかを提示してユーザーに確認してから `notion-create-database` を実行する。

## 推奨プロパティ

| プロパティ名 | 型 | 説明 |
|---|---|---|
| Name（タイトル） | Title | ベネフィット要約の見出し（例:「請求サイクルを月次/年次で選べるように」） |
| Category | Select | `Bug Fix` / `New Feature` / `Improvement` / `Breaking Change` |
| 対象範囲 | Multi-select または Text | テナント/プラン。「全テナント」「Enterpriseプランのみ」等 |
| 要約 | Text | 非エンジニア向け1〜2文 |
| 技術詳細 | Text | Issue/PR番号・リンク・担当者 |
| マイルストーン | Text または Relation | 元のマイルストーン名 |
| 公開日 | Date | Slack投稿日 or Notion公開日 |
| ステータス | Select | `Draft` / `Reviewed` / `Published` |
| Slackリンク | URL | 投稿後に埋める（Step 6の後で更新） |

既存DBがある場合は上記と完全一致させる必要はない。`notion-fetch`で既存スキーマを取得し、近いプロパティにマッピングする。無理に新規プロパティを増やさない。

## 作成/更新の手順

1. `notion-search`でDBの有無を確認
2. 無ければ上表を提示してユーザー確認 → `notion-create-database`
3. 各Issueについて`notion-create-pages`でレコードを1件ずつ作成（`parent`はDB ID、`properties`は上表に対応させる）
4. 既存レコードとの重複（同一Issue番号）がないか、作成前に`notion-search`または`notion-fetch`で確認する
