---
name: generating-release-notes
description: GitHub milestoneのIssue/PRを全件収集・重複除外・ラベル分類し、対象範囲を明記した社内版/社外版release notesを作る。Notion保存やSlack共有はユーザー確認後の明示依頼時だけ行う。
---

# リリースノート生成・配信

GitHub milestone単位の変更を、非エンジニアにも伝わるbenefit中心の文章と技術詳細の二層に整理する。既定ではローカルのMarkdown下書きまで進め、Notion/Slackの外部writeはレビュー承認後の明示依頼に限る。

## 接続と設定

- GitHubは `gh` CLIを使い、最初に `gh auth status` でprincipalを確認する。
- Notionは利用可能な `notion-search` / `notion-fetch` / `notion-create-database` / `notion-create-pages` などの接続済みtoolを確認する。
- Slackも接続済みtoolを確認する。
- いずれかが未接続なら、実行せず手動コピペ用Markdownを返す。

初回または未設定時は `.claude/release-notes.config.json` を読み、なければ次をAskUserQuestionで確定する。保存はユーザー確認後だけ行う。

1. 対象GitHub repo（複数可）
2. 既存Notion DBまたは新規作成。IDはsearchで確定し、schemaは `references/notion-schema.md` で確認する。
3. Slack投稿先channel

分類の対応は `references/classification.md`、文体は `references/writing-style.md`、Slack形式は `references/slack-format.md`、configは `references/config.md` を該当時だけ読む。

## 収集

milestone名/番号がなければ候補を提示して選んでもらう。

```bash
gh api repos/<owner/repo>/milestones
gh issue list --repo <owner/repo> --milestone "<milestone名>" --state all \
  --json number,title,body,labels,url,closedAt,assignees
gh pr list --repo <owner/repo> --search "milestone:\"<milestone名>\" is:merged" \
  --json number,title,body,labels,url,mergedAt
```

IssueとPRは次ページがなくなるまで取得し、query、取得ページ数、終端確認時刻、走査数を記録する。`--limit` やcursorを使う場合も、全ページ取得と終端確認を省略しない。canonical keyを `repo#number` として重複除外し、関係を確認できた場合だけ異なる番号も統合する。

各itemの状態を `merged/closed`、`released/available`、`unverified` に分ける。merge/closeはリリース済みや対象tenantで利用可能であることを意味しない。提供状態を確認できないものは公開候補に入れず「未提供または要確認」とする。

## 分類と文章

GitHub labelを正本に、`Bug Fix`、`New Feature`、`Improvement`、`Breaking Change`、`Internal（非公開）`へ分類する。labelなし・曖昧なものは推測せず「要確認」で保留する。InternalはNotion/Slack候補から除外する。

各公開候補に次を作る。

- **Benefit要約**: 1〜2文、非エンジニア向け。
- **対象範囲**: 全tenant、特定plan/契約、該当なしを明記。
- **技術詳細**: Issue/PRリンク、担当、変更の根拠。Notionでは折りたたみまたは別sectionに置く。

技術詳細や対象範囲を推測で埋めない。Issue/PR本文、label、available確認にない情報は未確認として残す。

## 必須レビューゲート

Notion/Slackへwriteする前に、全公開候補と次の根拠をチャットへ提示し、ユーザーの明示確認を取る。

- 全ページ取得と終端確認
- Issue/PRの重複除外
- label分類、Internal除外、要確認項目
- merged/closed と released/available の区別
- tenant/planの対象範囲

承認後も、生成、Notion保存、Slack投稿、GitHubのclose/releaseを別状態で記録する。対象・影響・公開範囲を広げる変更だけは具体化して再確認する。

## NotionとSlack

Notionは `notion-docs` の基本順序（search → fetch → create-pages / update-page）を使い、IDを推測しない。既存DBへの追記を基本とし、schema/property変更は別承認を取る。ページ状態 `Draft` / `Reviewed` / `Published` を混同せず、作成成功を公開済み・利用可能の証明にしない。

Slackは `references/slack-format.md` に従い、Benefit要約、対象範囲、Notion linkを含める。投稿直前にレビュー済み内容との一致を確認する。投稿成功はNotion表示、利用者確認、GitHub release、milestone closeを証明しない。

## 完了報告

Notion page/DB URL、Slack permalink、カテゴリ別件数、Internal除外数、要確認数、取得ページ数と終端確認、重複除外数、状態別件数を、生成・保存・投稿・表示確認の実績に分けて報告する。未確認の提供状態や承認を成功扱いしない。

## 禁止事項

- ユーザー確認なしにSlack投稿、Notion DB作成・更新、GitHubのclose/releaseを行う。
- Issue本文をそのまま非エンジニア向け文章として出す、tenant/plan範囲を省く、labelを推測する。
- Notion IDを推測する、最初のページだけで全件とみなす、Issue/PRを二重に公開する。
- merge/close、生成成功、通知成功だけでreleased/availableやPublished/Closedと判定する。
