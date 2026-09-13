---
name: generating-setup-wizards
description: サードパーティー設定・一度限りの移行・状態遷移を、人間が一段ずつ確認できる対話型 bash wizard にする。URLで値を取得し、.env または GitHub Actions secrets へ安全に書き込む手順に使う。
disable-model-invocation: true
---

# Wizard を生成する

手作業の設定や移行を、値の取得、確認、保存まで一段ずつ案内する bash スクリプトにする。既定は一時的な成果物で、反復可能な手順として残すのはユーザーが望む場合だけにする。

同梱の [template.sh](template.sh) には、進捗表示、確認ゲート、クロスプラットフォームの `open_url`、`ask` / `ask_secret`、冪等な `.env` upsert、`set_secret` / `set_var`、終了要約がある。`STAGES` マーカーより上のライブラリは編集しない。

## 1. 範囲を確定する

質問から始めず、まず対象リポジトリの `.env`、`.env.example`、`.env.*`、README、`docker-compose*`、設定、`.github/workflows/*` を読む。`secrets.*` と `vars.*` の参照、現在状態、目標状態、不可逆操作を洗い出す。

順序付き stage 一覧を示し、ユーザーの確認を得る。各値について次を決める。

- 人間がどこで取得するか
- `.env`、GitHub secret、両方、保存しない、のどこへ書くか
- secret として非表示入力するか、公開値か

## 2. stage を具体化する

各 stage に URL、画面上の操作、値の表示場所、保存する変数名を記す（例は実際に確認できる経路だけ）。現在の UI やコマンドを確認できない場合は捏造せず、質問または出典を残す。

一つの stage を一つの作業にし、`stage`、`say` / `step`、`open_url`、`ask` / `ask_secret`、`write_env`、`set_secret` / `set_var`、`pause` / `confirm` を使う。`TOTAL_STAGES` と `TOTAL_MINUTES` は正直な見積もりにする。

値を尋ねる前に URL を開き、secret には `ask_secret`、永続化する値には `write_env` を使う。`set_secret` は CI が実際に参照する値だけにし、不可逆操作の前には `confirm` を置く。各 stage の表示は前画面を消し、必要情報が画面外へ流れないようにする。

## 3. 検証と引き渡し

- `bash -n <script>`、利用可能なら `shellcheck`、`chmod +x <script>` を実行する。
- wizard を最後まで自動実行しない。値の取得、保存先、`set_secret` 名と CI の `secrets.*` 参照が静的に対応することを確認する。
- 実行方法と未確認の UI を報告する。反復可能な手順として残す場合だけ commit し README からリンクする。
