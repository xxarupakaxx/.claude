# Issue tracker：Local Markdown

この repo の issue と spec（PRD と呼ばれることもある）は、`.scratch/` 配下の markdown file として管理する。

## 規約

- feature ごとに一つの directory を使う：`.scratch/<feature-slug>/`
- spec は `.scratch/<feature-slug>/spec.md` とする。
- 実装 issue は `.scratch/<feature-slug>/issues/<NN>-<slug>.md` に ticket ごとに一つのファイルとして置き、`01` から番号を振る。
複数の ticket を一つにまとめたファイルは決して作らない。
- triage state は、各 issue file の先頭付近にある `Status:` 行へ記録する。
role の文字列は `triage-labels.md` を参照する。
- comment と会話履歴は、ファイル末尾の `## Comments` heading の下に追記する。

## skill が「issue tracker に公開する」と指示した場合

`.scratch/<feature-slug>/` 配下に新しいファイルを作る。
必要なら directory も作成する。

## skill が「関連する ticket を取得する」と指示した場合

参照された path のファイルを読む。
通常、ユーザーは path または issue number を直接渡す。

## Wayfinding 操作

`/mapping-large-projects` が使う。
**map** は一つのファイルであり、ticket ごとに一つの **child** file を持つ。

- **Map**：`.scratch/<effort>/map.md`。
Notes、Decisions-so-far、Fog を本文に持つ。
- **Child ticket**：`.scratch/<effort>/issues/NN-<slug>.md`。
`01` から番号を振り、本文に question を記す。
`Type:` 行に ticket type（`research`、`prototype`、`grilling`、`task`）を、`Status:` 行に `claimed` または `resolved` を記録する。
- **Blocking**：ファイル先頭付近の `Blocked by: NN, NN` 行。
列挙されたすべてのファイルが `resolved` になると ticket は unblocked になる。
- **Frontier**：`.scratch/<effort>/issues/` を走査し、open、unblocked、unclaimed のファイルを探す。
番号が最も小さいものを選ぶ。
- **Claim**：作業を始める前に `Status: claimed` を設定して保存する。
- **Resolve**：`## Answer` heading の下に回答を追記し、`Status: resolved` を設定する。
その後、gist と link からなる context pointer を `map.md` の Decisions-so-far に追記する。
