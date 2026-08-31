---
name: weekly-learning-review
description: 直近1週間のDaily、digest、trend、payment-trend、新規knowledgeノートを横断し、「今週なにを学んだか」を1枚の週次レビューノートに統合する。メタデータ監査（summary/related/depth欠落と孤立ノート）、LayerX入社準備の進捗確認、MOCへの接続提案を含む。「週次レビューして」「今週の学びをまとめて」「/weekly-learning-review」で起動する対話用スキル。
---

# /weekly-learning-review — 今週の学びを1枚に固める

> **スコープ**: このスキルは Obsidian Vault（`~/Notes/Vault`）でのみ有効。Vault 外のプロジェクトでは起動しない（`Daily/`、`Inbox/`、`Claude-note/` が存在せず、参照する絶対ルールと拡張フィールドの定義も Vault の `CLAUDE.md` にしかないため）。Vault 内には project scope の同名スキルがあり、そちらが優先される。

毎朝の自動収集（digest、trend、payment-trend）は「読んで終わり」になりやすい。
このスキルは週に一度、収集済みの情報を学びとして固め、[[AI-Agent-MOC]] や [[LayerX入社準備-MOC]] のグラフに接続し、メタデータの穴を可視化する。
**まず `CLAUDE.md` を読み絶対ルールとセカンドブレイン拡張フィールドの定義に従うこと。** 地の文は `japanese-tech-writing` の規範で書く。

入力: スキル起動時にユーザーが添えた指示（以下「起動時の指示」。slash command 経由なら `$ARGUMENTS` がそこに入る）

## 1. 対象週の決定と冪等性

- 起動時の指示に週（`2026-W28`）や日付があればその週。なければ**今日を含むISO週**（月曜起点）。
- 出力先: `Inbox/automation/weekly-review/weekly-review-YYYY-Www.md`。
- 同じ週のノートが既にあれば新規作成せず、各節を**追記**で更新する（週の途中で何度実行してもよい）。
- 実行開始時に `run_id`、対象週、今回の確認範囲（開始日・終了日）、前回のsource別cursor/watermarkを固定する。週途中の実行は月曜から実行日（または指定された締め日）までを `partial` として扱い、日曜まで確認していないのに週全体の学びとして断定しない。過去週でも未取得・未読の範囲があれば同様に明記する。
- 同じ週を再実行するときは、source path・日付・見出しまたはURLなどの安定した識別子と既存ノートのリンク／記録を照合する。既出項目は再度数えたり同じ要約を重ねたりせず、新規項目または確認済み範囲の差分だけを追記する。

## 2. 収集（検索ファースト。全文読みは絞った対象のみ）

1. scheduled / 無人実行では、path列挙や `rg` より前に `ruby _shared-ai/scripts/list-vault-automation-inputs.rb . Daily Inbox/automation/digest Inbox/automation/trends Inbox/automation/payment-trends Inbox/knowledge` を実行する。stdoutに出た許可済みpathだけを後続処理へ渡し、未filterのディレクトリを列挙しない。対話・on-demandでは、ユーザーが指定した範囲または既存の `rg -l "^date_created: <当週の各日付>"` の対象を使い、frontmatterの `summary` / `related` / `depth` / `tags` を回収する。
2. 系統別に要点を拾う:
   - `Daily/`: 「🔁 ふりかえり」「💭 メモ」節
   - `Inbox/automation/digest/`: 「概要」節
   - `Inbox/automation/trends/`: 当週ノートのTop見出し
   - `Inbox/automation/payment-trends/`: frontmatterの `learning_theme` と「基礎ノートへの接続」節
   - 当週の新規 knowledge / note: `summary`（なければ冒頭段落）
3. `Claude-note/` は書き込まない。scheduled / 無人実行では読み取り、リンク追跡、要約、NextActionsへの言及を行わない。対話・on-demandでユーザーが対象を明示した場合だけ、Vaultの境界に従って読み取り対象にできる。
4. `automation_read: false` または `source_system: claude-note` のノートは、scheduled / 無人実行で列挙、本文読取、リンク追跡、要約の対象外にする。
5. `Daily`、digest、trend、payment-trend、knowledgeをsource別に、処理窓・cursor/watermark・`success`・`normal-empty`（allowlist、対象日、必要なページングまで確認した正常な空結果）・`failed`・`unread` で記録する。`success` または確認済みの `normal-empty` だけ進捗を進め、取得不全・失敗・未読では前回位置を保持して未処理範囲と再開条件を残す。

## 3. 週次レビューノートの生成

frontmatterは拡張スキーマを使う（`type: note`、`tags: [automation, weekly-review, second-brain, learning]`、`summary`、`depth: overview`、`as_of: <実行日>`、`related` に当週の主要ノートとMOC）。

本文の構成:

```md
## 対象範囲と収集状態
（run_id、対象週、今回の確認済み日付範囲、source別のcursor/watermarkと success / normal-empty / failed / unread。未読・未取得範囲と再開条件も記録する）

## 今週の学び
（テーマ別に最大5項目。各項目は1〜3文で「何がわかったか」を書き、根拠ノートへ [[リンク]] する）

## LayerX入社準備の進捗
（payment-trendのlearning_theme一覧、基礎ノートへ接続できた/できなかった話題、簿記や議事録などその他の学習活動）

## 今週の数字
（系統別の作成ノート数。Daily / digest / trend / payment-trend / knowledge / その他。確認済みと未読・未取得を分ける）

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
- このcadenceや登録情報は設定の案内であり、runの起動、Vaultへの保存、完了報告・通知の成功を意味しない。各状態を実際の実行記録で分け、週途中・failed・unreadのrunを完了週として報告しない。
