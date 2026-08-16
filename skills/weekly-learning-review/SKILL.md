---
name: weekly-learning-review
description: 直近1週間のDaily、digest、trend、payment-trend、新規knowledgeノートを横断し、「今週なにを学んだか」を1枚の週次レビューノートに統合する。メタデータ監査（summary/related/depth欠落と孤立ノート）、LayerX入社準備の進捗確認、MOCへの接続提案を含む。「週次レビューして」「今週の学びをまとめて」「/weekly-learning-review」で起動する対話用スキル。
---

# /weekly-learning-review — 今週の学びを1枚に固める

毎朝の自動収集（digest、trend、payment-trend）は「読んで終わり」になりやすい。
このスキルは週に一度、収集済みの情報を学びとして固め、[[AI-Agent-MOC]] や [[LayerX入社準備-MOC]] のグラフに接続し、メタデータの穴を可視化する。
**まず `CLAUDE.md` を読み絶対ルールとセカンドブレイン拡張フィールドの定義に従うこと。** 地の文は `japanese-tech-writing` の規範で書く。

入力: $ARGUMENTS

## 1. 対象週の決定と冪等性

- $ARGUMENTS に週（`2026-W28`）や日付があればその週。なければ**今日を含むISO週**（月曜起点）。
- 出力先: `Inbox/automation/weekly-review/weekly-review-YYYY-Www.md`。
- 同じ週のノートが既にあれば新規作成せず、各節を**追記**で更新する（週の途中で何度実行してもよい）。

## 2. 収集（検索ファースト。全文読みは絞った対象のみ）

1. 当週作成ノートの列挙: `rg -l "^date_created: <当週の各日付>"` を `Daily/` と `Inbox/`（`Claude-note/` は対象外）に対して実行。frontmatterの `summary` / `related` / `depth` / `tags` も `rg` で回収する。
2. 系統別に要点を拾う:
   - `Daily/`: 「🔁 ふりかえり」「💭 メモ」節
   - `Inbox/automation/digest/`: 「概要」節
   - `Inbox/automation/trends/`: 当週ノートのTop見出し
   - `Inbox/automation/payment-trends/`: frontmatterの `learning_theme` と「基礎ノートへの接続」節
   - 当週の新規 knowledge / note: `summary`（なければ冒頭段落）
3. `Claude-note/` は**読み取りのみ**。必要ならNextActionsの状況を1行で言及してよいが、書き込みは絶対にしない。

## 3. 週次レビューノートの生成

frontmatterは拡張スキーマを使う（`type: note`、`tags: [automation, weekly-review, second-brain, learning]`、`summary`、`depth: overview`、`as_of: <実行日>`、`related` に当週の主要ノートとMOC）。

本文の構成:

```md
## 今週の学び
（テーマ別に最大5項目。各項目は1〜3文で「何がわかったか」を書き、根拠ノートへ [[リンク]] する）

## LayerX入社準備の進捗
（payment-trendのlearning_theme一覧、基礎ノートへ接続できた/できなかった話題、簿記や議事録などその他の学習活動）

## 今週の数字
（系統別の作成ノート数。Daily / digest / trend / payment-trend / knowledge / その他）

## メタデータ監査
（当週の新規ノートのうち summary なし・related なし・depth なしの件数と一覧。全期間の孤立ノート（リンク0）も件数を出す）

## MOCへの接続
（当週の新規knowledgeでMOC未接続のものに接続先を提案する。対話中なら承認を得て、該当ノート末尾への追記まで実行してよい）

## 来週のフォーカス
（1〜3個。問いの形で書く）
```

## 4. リンクとゲート

- 実行日の `Daily/YYYY-MM-DD.md` の「💭 メモ」に `- 📅 週次レビュー: [[weekly-review-YYYY-Www]]` を**追記**（当日Dailyがなければテンプレートから実値で作成）。
- 既存ノートへの変更は**末尾または節内への追記のみ**。リネームと削除はしない。新規ノートは `Inbox/` 配下のみ。
- 保存前に [[04_verifier]] の観点で自己検証する: YAMLが壊れていないか、`[[wikilink]]` が実在ノートを指すか、Templater記法が残っていないか。

## 5. 報告

学びのトップ3、メタデータ監査の件数、生成したレビューノートへのリンクを短く返す。

## ⏰ スケジュール設定

- **主モードは on-demand**（対話で呼ぶ）。定期実行では金曜09:15の `/loop-engineering` の後、金曜18:00に週1回実行する。
- Codex automation id: `weekly-learning-review`。cadence例は `0 18 * * 5`。
