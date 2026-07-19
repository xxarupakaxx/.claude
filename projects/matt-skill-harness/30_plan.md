# 実装計画

## Task 1：採用境界を確定する

- `batch-grill-me` と `to-questionnaire` の package、license、起動権、外部副作用を確認する。
- 41 Skill inventory の判定を、導入、既存対応、削除、保留に更新する。
- verify：同じ upstream revision と local adaptation が証拠で結ばれている。

## Task 2：正式名の discovery surface を作る

- `wayfinder`、`to-spec`、`to-tickets`、`implement`、`teach` を user-invoked 入口として追加する。
- 既存の日本語実装を規律の正本として参照し、同じ model-invoked trigger を重複させない。
- verify：名前で検索でき、明示起動以外では自動起動しない。

## Task 3：in-progress Skill を隔離導入する

- `batch-grill-me` は複数質問を一度に答えたい場合だけ使う。
- `to-questionnaire` は local Markdown を作るだけとし、送信や tracker 投稿を行わない。
- in-progress 状態と代替となる安定 Skill を本文に表示する。
- verify：representative prompt、非起動 prompt、安全境界のテストが通る。

## Task 4：deprecated Skill を削除する

- `design-an-interface`、`conducting-quality-assurance`、`planning-refactors`、`ubiquitous-language` の参照を置換先へ移す。
- selector、registry、estate を更新してから Skill directory を削除する。
- `handing-off-to-claude` は deprecated ではないため、今回の削除対象から外す。共有 routing から外れていることだけ確認する。
- verify：削除名への active route と runtime path が0件になる。

## Task 5：ロードマップを一画面で判断できる形へ絞る

- first screen を Now、Next human decision、Coverage、Outcome Trace に限定する。
- Outcome Trace に Human Review と Objections を追加する。
- tasks、phases、artifacts、logs は details に折りたたむ。
- Planned、Observed、Revised、Verified を区別する Revision Log を追加する。
- verify：desktop、tablet、mobile、keyboard、色覚に依存しない状態表示を確認する。

## Task 6：teach 用の図解を作る

- ロードマップの読み方を一枚の状態図と対応表で説明する。
- 「ファイルがあるだけで完了か」「計画変更は失敗か」などの反論を evidence shortcut と結び付ける。
- 小テストで漏れと再検証の判断を確認する。
- verify：lesson と reference が単独で開き、ロードマップから到達できる。

## Task 7：governance 基盤を修正する

- live catalog の人間向け出力が欠損フィールドで落ちないようにする。
- audit、parity、delivery、roadmap test を fresh に実行する。
- verify：両 user-scope repo で同じ結果になる。

## Task 8：user-scope を昇格する

- `.codex` を先に commit、push する。
- `.claude-global` を同じ意味へ同期し、commit、push する。
- live `~/.codex` と `~/.claude` の runtime-only file を保護して fast-forward する。
- Vault は submodule pointer だけを commit、push する。
- verify：exact SHA、clean tracked state、runtime-only file 保持を確認する。
