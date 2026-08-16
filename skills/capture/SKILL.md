---
name: capture
description: 会話/自由テキストで渡した読書感想・気づき・URLを、適切なノート(reading/note/knowledge)に整形し外部補完してObsidianに保存・リンクする会話用キャプチャ
---

# /capture — 会話でそのまま放り込む

OCRや手入力フォームを使わず、**話した/打ったテキストをそのまま**渡すだけで適切なノートに整理する。対話セッション（claude.ai/code・モバイル・Slack）で使う想定。**まず `CLAUDE.md` を読み絶対ルールを守ること。** 詳細手順は `Inbox/automation/playbooks/`（[[AI-Bullpen-Vault]]）。

入力: $ARGUMENTS

## 入力の取り方（対話 / 無人の両対応）
- **対話時**（$ARGUMENTSあり or 直前の私の発言）: それを入力として処理。曖昧で重要な点だけ1問確認し、他は即実行。
- **無人スケジュール時**（$ARGUMENTSが空 & 会話文脈なし）= "capture-sweep": **デイリーノートが唯一の受け皿**。`Daily/`（今日＋直近数日）の `## 💭 メモ` / `## ✅ タスク` 等に人間が貼ったURLや書いた一行（「『〇〇』読んだ」「後で読む」等）の**未処理分**を入力として処理する。各項目は処理後、その行の直下に `    - → 整理済み [[ノート名]]` を**追記**（行は消さない＝冪等）。`→ 整理済み`/`→ 要約済み` が既に付く項目はスキップ。
  - ※ これは [[daily-curator|/daily-curator]] §5 と同じ「デイリー→自動要約」を、朝を待たず日中にも回すための軽量版。
  - （任意）`Inbox/quick-capture.md` やSlack保存メッセージを別口として足してもよいが、**基本はデイリーノートだけでよい**。

## 1. 意図を分類
- **読書/視聴の感想**（「『〇〇』読んだ」「あの記事良かった」等）→ `type: reading`
- **気づき・アイデア・考え**（書名なし）→ `type: note`
- **URL＋コメント** → [[05_url-knowledge]] の流れ（後で読む/読んだ）
- **調べて / まとめて / 比較して / 理解しておきたい / 見ておく** → [[09_daily-research-requests]] の流れ。AIが処理できるものは `Inbox/knowledge/` に調査ノート化し、本人アカウントや非公開情報が必要なものは `[!]` として残す。
- 複数混在ならそれぞれ作る。

## 2. ノート作成（自分の層は脚色しない）
- reading は `templates/reading.md`、note は `templates/note.md` を元に `Inbox/`（読書/知見は `Inbox/knowledge/`）へ新規作成。`<% %>` は実値置換、`tp.file.cursor()` 削除。ファイル名は内容ベースで一意に。
- テンプレートにある `summary`（1行要約・`"..."` 囲み）と `related`（`"[[ノート名]]"` の配列）を必ず埋める。知見ノートは `templates/knowledge.md`（`type: knowledge`、`depth` は通常 `overview`）を使う。定義は CLAUDE.md「セカンドブレイン拡張フィールド」。
- **本人が言ったことだけを本人の層**（要点・感想）に書く。言っていないことを足さない。書名/著者が不明で必要なら1問だけ聞く。
- **図の活用（Mermaid）**：技術的なURLや記事で処理フロー・比較・アーキテクチャを説明する場合は、テキストだけより Mermaid で図示した方が分かりやすいときに使う（` ```mermaid ` コードブロック、ObsidianはMermaidをネイティブでレンダリングする）。

## 3. 外部補完 & 基盤化（reading/知見のとき）
- [[07_reading-enrich]] を適用: `## 🌐 外部コンテキスト（AI補完/要検証）` を `WebSearch`/`WebFetch` で出典付き補完（著者背景・関連概念・対立見解・原典）→ キー概念を概念ノート化し双方向リンク＋[[Concepts-MOC]]追記 → `## 🧠 統合メモ` で自分の言葉×外部×既存ノートを突き合わせFB。
- 外部補完や調査ノート化で一次情報確認が必要な場合は、`research` スキルを使い、出典付きMarkdownを `Inbox/knowledge/` に残す。
- ネットワーク制限で取得できない場合は補完を空欄にし `[!]` をbacklogに残す（原文ノートは保存する）。

## 4. リンク & ゲート & 保存
- 今日の `Daily/YYYY-MM-DD.md` の `## 💭 メモ` から作成ノートへリンクを**追記**（無ければ当日Dailyを作成）。アクションがあれば `## ✅ タスク` に `- [ ]`。
- [[03_guardian]]（リネーム/削除なし・Inbox配下・CLAUDE.md不変）→ [[04_verifier]]（YAML/wikilink/`<% %>`残り）。
- `main` にコミットし、`origin/main` へpushする。

## 5. 報告
- 作ったノート名、補完した外部コンテキストの要点、繋いだ概念、Dailyのリンク先を一言で返す。

## ⏰ スケジュール設定
- **主モードは on-demand**（会話・モバイル・Slackでその場で呼ぶ）。定期実行は必須ではない。
- 定期で「日中の走り書きを溜めずに捌く」なら **capture-sweep** をRoutine化:
  - prompt: `/capture` ／ repo: `obsidian-vault`
  - cadence: 日中3時間おき（例 平日 09–21時）。フォーム presetは hourly を選び、`/schedule update` で cron `0 9-21/3 * * 1-5`（最小間隔1h・TZ要確認）。
  - connectors: 不要（Slack保存メッセージも入れるならSlackのみ）／ network: 外部補完を使うなら **Full**／ model: `gpt-5.5` / service_tier: `priority`
  - 入力源: **デイリーノート**（`Daily/` 今日＋直近の `## 💭 メモ` 等の未処理項目）。別口の `Inbox/quick-capture.md` は任意。
- ⚠️ [[daily-curator|/daily-curator]] の朝スイープがデイリー本文・添付・各ソースを拾うため、**capture-sweepは任意**（重複処理は冪等マークで回避）。詳細・各コマンド一覧 → [[SCHEDULES]]
