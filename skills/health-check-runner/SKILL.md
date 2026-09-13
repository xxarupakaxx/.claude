---
name: health-check-runner
description: Inbox/knowledge の Second Brain を、出典・孤立・MOC到達性・as_of鮮度・拡張スキーマ・重複候補の6項目で機械点検し、結果をヘルスチェックノートへ追記する月次またはオンデマンドの対話用スキル。「ヘルスチェックして」「月次点検」「/health-check-runner」で使う。
---

# /health-check-runner

まず適用対象の `CLAUDE.md` とプロジェクト正本を読み、追記のみ、新規は Inbox 配下、`Claude-note/` 不可侵のルールに従う。対象は `Inbox/knowledge/` 配下（ダッシュボードと同じ範囲。README と MOC 自身は除く）で、件数は目視せずスクリプトで測る。

## 点検項目

1. **出典なし候補**：frontmatter に `url` / `source` / `evidence_urls` がなく、本文にも「出典」「根拠URL」「参考」「公式リンク」見出しがないノート。自分の考えだけのノートは問題と断定せず候補として出す。
2. **孤立ノート**：アウトリンク0本。
3. **MOC到達性**：4つの MOC から無向 BFS で距離3以上のノート。距離判定は [[moc-gardener]] と同じ。
4. **as_of鮮度**：`as_of` が6か月以上前。
5. **拡張スキーマ**：`summary` / `related` / `depth` の欠落数。digest、trends、payment-trends の直近出力も確認する。
6. **重複候補**：summary が酷似する組だけ挙げ、矛盾の判断は人間へ残す。

各項目に、次を別々に記録する。

- **機械判定**：件数、対象 path、実行時点、`PASS` / `EMPTY` / `FAIL` / `UNREAD`
- **内容確認**：主張、出典の支持、矛盾、重複、鮮度を人が確認したか
- **利用可能性**：詳細ノートの path・リンク・表示内容を開けたか
- **確認導線**：問題ごとの次の Skill、人間の判断、再確認条件

`PASS` や生成成功だけで、本文の正しさ・利用可能性・対応完了とは扱わない。

## 記録と報告

1. `Inbox/automation/health/health-check-YYYY-MM-DD.md` を作る。全件一覧を含め、少なくとも「機械実行」「内容確認」「利用可能性」「確認導線」を分ける。
2. [[Second Brain ヘルスチェック]] の「## 記録」節へ、`### YYYY-MM（機械実行 YYYY-MM-DD）` の月見出しと件数サマリ、詳細ノートへのリンクだけを追記する。既存記録とチェックボックスは変更しない。
3. 件数、前回との差、詳細ノートへのリンク、4つの判定状態を短く報告する。修正候補には [[moc-gardener]] または [[vault-metadata-migrator|vault-metadata-migrator]] への導線を添える。

検出した問題の修正、Close、外部公開はこの Skill で行わない。リネーム・削除もしない。主モードは on-demand、定期化する場合は人間が [[SCHEDULES]] の手順で月初に登録する。
