---
name: capture
description: 会話の読書感想・気づき・URLをreading/note/knowledgeへ分類し、必要な外部補完とDailyリンクを加えてObsidianへ保存する。`/capture`、またはDailyの未処理メモを拾うcapture-sweepで使う。
---

# /capture

話した・打ったテキストを、本人の言葉を保ったノートへ整理する。最初に対象の `CLAUDE.md` と `_shared-ai/knowledge/vault-operation-contract.md`、詳細手順が必要なら `Inbox/automation/playbooks/` を読む。リネーム・削除をせず、既存ノートは追記に限る。

入力は起動時の指示（slash command 経由なら `$ARGUMENTS`）または直前の発言。

## 入力モード

- **対話**: 入力を処理し、結果が変わる重要な不明点だけ1問確認する。
- **capture-sweep**: 引数・会話文脈が空の無人実行。今日＋直近数日の `Daily/` の `## 💭 メモ` / `## ✅ タスク` などから、人間が書いた未処理行だけを拾う。`→ 整理済み` / `→ 要約済み` がある行は省く。

sweep開始時に `run_id`、対象Daily、処理window、前回marker/source位置を固定する。sourceごとに `success`、`normal-empty`、`failed`、`unread` を記録し、successまたは確認済みnormal-emptyだけ位置を進める。失敗・不完全読み取り・未読は次回へ残す。同じwindowではcanonical URL、既存ノート、Daily backlink、markerを照合し、二重作成しない。部分失敗を行全体の成功にしない。

## 意図を分類

| 入力 | 処理 |
| --- | --- |
| 書名・記事名と感想 | `type: reading`（Vaultのreading template） |
| 書名なしの気づき・アイデア | `type: note`（Vaultのnote template） |
| URLとコメント | `[[05_url-knowledge]]` のURL導線 |
| 調べて/まとめて/比較して等 | `[[09_daily-research-requests]]`。可能なら`Inbox/knowledge/`、本人アカウント・非公開情報が必要なら`[!]`で保留 |

混在入力は単位ごとに分ける。書名や著者が必要だが不明なら1問だけ聞く。

## ノート作成

読書・note・knowledgeは対応するtemplateを使い、指定がなければ `Inbox/`、知見は `Inbox/knowledge/` に新規作成する。Templaterの `<% %>` を実値へ置換し、`tp.file.cursor()` を残さない。ファイル名は内容に基づき既存と衝突させない。

本人が言った要点・感想だけを本人の層へ書き、AI補完を混ぜない。templateの `summary`（1行・引用符付き）と `related`（`"[[ノート名]]"` 配列）を埋める。knowledgeは `type: knowledge`、`depth: overview` を通常値とし、定義はVaultの拡張fieldを正本にする。

技術URLや記事でflow・比較・architectureを示すと理解が上がる場合だけ、自己完結SVGを `attachments/` に置いて `![[ファイル名]]` で参照する。Mermaidは新規生成しない。

## 外部補完

reading/knowledgeだけ、必要に応じて `[[07_reading-enrich]]` を使い、`## 🌐 外部コンテキスト（AI補完/要検証）` にWebSearch/WebFetchの出典付き情報を置く。著者背景、関連概念、対立見解、原典を本人の感想と分ける。概念ノート化、双方向link、`[[Concepts-MOC]]` 追記は依頼範囲に含まれる場合だけ行う。一次情報確認が必要なら `research` に渡す。

外部取得・概念link・検証の一部が失敗したら、その項目を整理済みとしない。保存できた原文には `→ 要確認` / `→ 保留` と `[!]` backlog、失敗内容、再開条件を残す。

## backlink、marker、gate

作成ノートのlinkを当日 `Daily/YYYY-MM-DD.md` の `## 💭 メモ` に追記する。Dailyがなければ作成し、アクションは `## ✅ タスク` に未完了checkboxで追記する。capture-sweepの元行は削除せず、その直下へ次を追記する。

```text
    - → 整理済み [[ノート名]]
```

このmarkerは、必要なノート保存、Daily backlink、依頼された外部補完、`[[03_guardian]]` と `[[04_verifier]]` が全て成功した後だけ付ける。Guardianはリネーム/削除、Inbox外新規、`CLAUDE.md`変更を確認し、VerifierはYAML、wikilink、Templater残りを確認する。失敗・未読・未確認なら成功markerを付けない。

Vault外へ収集物を送らない。commit/pushが現在の依頼またはproject policyに含まれる場合だけ、対象ファイルを分離して実行し、成果物・検証・commit・push・通知を別状態で報告する。

## 報告とschedule

作成ノート、外部補完の要点、概念link、Daily backlink、未処理/失敗と再開条件を短く返す。

主モードはon-demand。capture-sweepを定期化する場合は人間が `[[SCHEDULES]]` の手順で登録する。日中3時間おきなどのcadence、Full network、Slack connector、modelは設定案内であり、起動・取得・保存・marker更新・通知の成功を意味しない。`daily-curator` と入力が重なる場合もmarkerで冪等性を保つ。
