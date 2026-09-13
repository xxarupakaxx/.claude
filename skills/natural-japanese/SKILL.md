---
name: natural-japanese
description: 仕事の日本語や記事を、内容と書き手の声を保ったまま自然で読みやすく書く・直す。議事録、報告、ガイド、メール、記事の執筆・推敲、AI臭さの診断に使い、Markdownの構造整形だけには使わない。
license: MIT
argument-hint: "[write|score] [quick|full|exp] [対象ファイルや依頼内容]"
---

# natural-japanese

日本語の文書を、読者が要点を追えて書き手の声も残る形に整える。体験、数値、固有名詞、引用、留保は創作・改変しない。自然な箇所は残し、一般論、前置き、重複、機械的な対比や列挙を必要な範囲で削る。

## 呼び出しとルーティング

- `/natural-japanese [quick|full] <対象>`: 既存文書を直す（既定は `quick`）。
- `/natural-japanese write [quick|full] <題材や素材>`: 素材から新規に書く。
- `/natural-japanese score [quick|full|exp] <ファイル>`: 書き換えず自然度を診断する。

明示がなければ、短い日常文書は `quick`、対外・経営向けまたは長い文書は `full` とする。ジャンルや目的が不明で結果が変わる場合だけ確認する。

## write: 設計・執筆・検査

まず読者、読後に起こしたいこと、文書タイプ、主メッセージを定め、見出しだけで論旨を追えるスケルトンを作る。既存の文体プロファイルがある場合だけ読み込む。新規執筆で素材が足りないときは検索またはユーザーへの確認に戻り、事実を埋めない。

文体は `references/writing-constitution.md` の要点（結論を先に置く、見出しをメッセージにする、専門語を初出で説明する、固有名詞・数値で接地する、事実と推測を分ける、濃淡を残す、同じ型を繰り返さない）に従う。元原稿の声、リズム、留保、ユーモアを保つ。

### quick（既定）

1. 文書タイプが決まれば、対応する型を一つだけ読む。
2. 本文を作成または改稿する。
3. `uv run scripts/lint.py --json <file>` を一度実行する。ジャンルが明確なら `--genre essay|tech|business` を付ける。
4. lint の finding は文脈で採否を判断し、スケルトンと本文を通読する。新しい問題がなければ最終通読で終える。

### full

quick の工程に加え、`scripts/outline.py` と `scripts/terms.py` を実行し、構造・読みやすさ・文書タイプのレビューを行う。レビューを委譲する場合も、判断台帳への統合と「直す／残す」の決定は親が行う。必要な finding が整理され、修正が新しい問題を生まないまで収束させる。

収束ループでは直前の `--json` 出力を `--baseline` に渡して resolved / new / persisting を比較できる。読解負荷だけを調べる場合は `uv run skills/natural-japanese/scripts/lint.py --reading-load <ファイル>` を使い、findingを文脈で判断する。

## score: 診断だけ

最初に `references/diagnose.md` を読み、そこで定義された自然度スコア（0〜100、高いほど自然）と出力形式を使う。`quick` は lint、`full` は構造・読みやすさのレビュー、`exp` は追加で `scripts/semantic.py --json <file>` を使う。`semantic.py` は重量級の依存と初回モデル取得を伴うため、明示された `exp` のときだけ実行する。

score では原稿を書き換えない。finding の転記をスコアの代わりにせず、スコア、根拠、目立つ箇所、必要なら改稿提案だけを返す。改稿はユーザーが依頼してから行う。

## 参照の読み分け

必要なものだけを開く。

| 状況 | 参照 |
| --- | --- |
| 議事録・レポート・ガイド・メモ・スライド | 文書の用途に合う補助資料が存在する場合だけ該当資料を読む |
| lint の判断、収束、素材不足、自己点検 | `references/revision-guide.md` |
| 禁止語・翻訳調・読みやすさの判断 | `references/forbidden-patterns.md`、`references/translationese.md`、`references/readability-principles.md`、`references/readability-antipatterns.md` を該当 finding のときだけ |
| ジャンル閾値・手作業検査 | `references/genre-notes.md`、`references/manual-checklist.md` |
| score | `references/diagnose.md` |
| ユーザーの文体プロファイル作成 | `assets/style-profile-template.md` |

型に合わない note・ブログ・エッセイは doctype 参照を省く。技術文書の一文一行化、引用ブロック、脚注、Mermaidなどの構造設計は別スキルへ渡す。

## 検査と完了条件

lint は疑いを提示するだけで、全件修正を強制しない。各 finding と構造レビューの指摘について、修正したか、残す理由を判断台帳に残す。本文を見出しと段落冒頭だけで読んでも論旨が通り、見出しが内容を伝え、結びが読者の次の判断につながることを確認する。

最終パスでは初見の読者として全文を読み、語順、係り受け、一文の焦点、段落の濃淡、作者の声を確認する。追加した作業用の台帳・lint JSON・下書きバックアップは、ユーザーが求めない限り残さない。変更後のMarkdownは全文を再読する。
