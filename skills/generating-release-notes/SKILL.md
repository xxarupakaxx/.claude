---
name: generating-release-notes
description: GitHubマイルストーンに紐づくIssue/PRを収集し、bug fix / new feature / improvement等に分類した上で、非エンジニアにも伝わるリリースノートを作成してNotion DBに蓄積し、Slackで共有する。マルチテナントSaaSでの対象範囲（テナント/プラン）明記と、社内版（技術詳細）/社外版（ベネフィット訴求）の二層フォーマットに対応。「リリースノート作って」「マイルストーンの内容をまとめて」「今週のアップデートをSlackに共有して」「Notionにリリースノート溜めたい」「今週何ができるようになったか教えて」等の依頼、またはGitHubマイルストーンをクローズした直後に使用。
---

# リリースノート生成・配信スキル

GitHub Milestone単位でIssue/PRを分類し、非エンジニア（営業・ディレクター）にも伝わる形でNotion DBに蓄積し、Slackで共有する。

## 設計原則（背景）

- **changelog（エンジニア向け・密）と release notes（非エンジニア向け・ベネフィット先出し）を分離する**。1つのIssueから両方を生成し、Notionページ内で技術詳細を折りたたむ/別セクションにする二層構造にする。
- **対象範囲（テナント/プラン）を毎回明記する**。マルチテナント前提のため「全テナント対象」「特定プラン限定」を省略しない。
- **分類はGitHub側のラベルを正本にする**。曖昧な場合は推測で書かず、ユーザーに確認する。
- 詳しい根拠は `/Users/yoshiki/Notes/Vault/Inbox/knowledge/リリースノート運用_マルチテナントSaaSの一次情報調査.md` の一次情報調査を参照可能（Vault内にある場合のみ。無ければ参照しない）。

## 前提・接続確認

- GitHub: `gh` CLI（Bashツール経由）。`gh auth status` でprincipal確認。
- Notion: Notion MCPツール（`notion-search` / `notion-fetch` / `notion-create-database` / `notion-create-pages` 等。完全修飾名は接続IDにより環境依存なので、呼び出し前に `ToolSearch` で `select:` 検索するか、`notion-docs` スキルの手順に委譲する）
- Slack: Slack MCPツール（`slack_send_message` 等、同上）
- いずれか未接続の場合はユーザーに案内し、代替（手動コピペ用のMarkdown出力のみ）を提案する

## Step 0: 設定確認（初回 or 未設定時）

次の3項目を確認する。プロジェクトディレクトリに `.claude/release-notes.config.json` があれば読み込み、無ければ `AskUserQuestion` で聞いて保存を提案する（保存はユーザー確認後のみ。詳細は `references/config.md`）。

1. **対象GitHubリポジトリ**（複数可）
2. **Notion DB**: 既存を使うか新規作成するか。既存なら `notion-search` でIDを確定（推測禁止）。新規ならプロパティ設計を提示し確認を取ってから作成（`references/notion-schema.md`）
3. **Slack投稿先チャンネル**: 専用チャンネルか既存チャンネルかはユーザーの意思決定事項。このスキルは決めず、チャンネル名をパラメータとして受け取る

## Step 1: マイルストーン特定 & Issue/PR収集

IssueとPRは各queryの全ページを、次ページがないことを確認するまで取得する。`--limit` やcursorを使う場合も、取得ページ数、query、実行時点、終端条件を記録し、最初のページだけで網羅済みとしない。空のページは、次ページがないことを確認できた場合だけ「確認済み空」とする。

IssueとPRを同じrelease itemへ二重に数えない。canonical keyを `repo#number` として同じ番号をdedupeし、IssueとPRの両方が一つの変更を示す場合は一つのベネフィット項目にまとめ、技術詳細へ両方のリンクを残す。異なる番号を同じ変更とみなす場合は、本文やGitHubの関連付けで関係を確認できたときだけ統合し、確認できなければ「要確認」として保留する。

IssueのcloseやPRのmergeは収集上の状態であり、リリース済み・対象テナントで利用可能であることを意味しない。各itemに `merged/closed`、`released/available`、`unverified` の状態を記録し、利用可能性を確認できないものを提供済みとして公開候補へ含めない。

```bash
gh issue list --repo <owner/repo> --milestone "<milestone名>" --state all \
  --json number,title,body,labels,url,closedAt,assignees
gh pr list --repo <owner/repo> --search "milestone:\"<milestone名>\" is:merged" \
  --json number,title,body,labels,url,mergedAt
```

マイルストーン名/番号が未指定なら `gh api repos/<owner/repo>/milestones` で候補を提示し選ばせる。

## Step 2: 分類

ラベルベースでカテゴリ分類する。詳細マッピングとラベルが無い場合の扱いは `references/classification.md` を読むこと。

- 分類先: `Bug Fix` / `New Feature` / `Improvement` / `Breaking Change` / `Internal（非公開）`
- ラベルが無い/曖昧なIssueは「要確認」として一覧提示し、ユーザーに割り振ってもらう。推測で確定しない
- `Internal` に分類したものはNotion/Slackへの公開対象から除外する
- 収集状態が `merged/closed` だけのIssue/PRは、`released/available` を確認できるまで公開候補に含めず、「未提供または要確認」として残す

## Step 3: 非エンジニア向け文章生成

各Issueについて次の3点セットを作る。文体ガイドと具体的なBefore/After例は `references/writing-style.md` を読むこと。

1. **ベネフィット要約**（1〜2文、非エンジニア向け、専門用語を避ける）
2. **対象範囲**（全テナント / 特定プラン・契約 / 該当なし、を明記）
3. **技術詳細**（Issue/PR番号・リンク、担当者。エンジニア向け折りたたみセクション）

加えて、各itemの提供状態（merge/close、release、対象テナント・プランでの利用可能性）と、未確認の範囲を記録する。生成した文章は「提供済み」を推測して書かない。

## Step 4: ユーザーレビュー（CRITICAL・必須ゲート）

Notion/Slackへ実際に書き込む前に、生成した内容（Step 3の3点セット全件）をチャット上に一覧提示し、ユーザーの明示確認を取る。これは外部への投稿・DB更新に該当するため省略できない。

レビューでは、全ページを取得した根拠、Issue/PRの重複除外、提供状態、対象範囲、`Internal`除外、未確認項目を確認する。すでに承認された対象と影響の範囲内で同じ内容を各ページ・各チャンネルへ反映する場合、段階ごとの一律な再承認を追加しない。対象・影響・公開範囲を広げる場合だけ、変更内容を具体化して再確認する。

- 内容の修正依頼があれば反映してから次に進む
- `Internal` 分類したIssueが公開候補に紛れ込んでいないか、ここで最終確認する
- 生成、Notionへの保存、Slack公開、GitHubのIssue/MilestoneのCloseは別状態として扱い、レビュー承認だけで後続状態へ進めない

## Step 5: Notion DBへの書き込み

`notion-docs` スキルの基本パターン（search → fetch → create-pages / update-page）に従う。IDは必ずsearch/fetchで確定し、推測しない。

- DBスキーマ・1レコードの単位（1機能=1レコード推奨）は `references/notion-schema.md` を読むこと
- 既存DBへの追記が基本。プロパティ変更は破壊的なのでユーザー確認必須
- Notionページの生成・更新は `Draft` / `Reviewed` / `Published` の状態を混同せず、作成成功だけで公開済み・利用可能とは扱わない

## Step 6: Slack投稿

投稿フォーマットとチャンネル運用の判断材料は `references/slack-format.md` を読むこと。

- 非エンジニア向け要約を中心に、各Notionページへのリンクを添える
- 対象範囲を必ず明記する
- 投稿前にStep 4のレビュー済み内容と一致しているか確認する
- Slackの投稿成功は、Notionページの表示確認、利用者の確認、GitHubのrelease提供、Issue/MilestoneのCloseを証明しない。各状態と実際の確認結果を別に記録する

## Step 7: 完了報告

- 作成/更新したNotionページ・DBのURL
- Slack投稿のパーマリンク
- カテゴリ別件数、除外（Internal）件数、要確認のまま残った件数
- 取得ページ数と終端確認、重複除外件数、提供状態別件数、Notion/Slackの実行結果、内容確認と利用可能性の確認を分けて報告する。未確認の提供状態やユーザー確認を成功扱いにしない

## Anti-Patterns（禁止事項）

- ユーザー確認なしにSlackへ投稿する、またはNotion DBを新規作成する
- Issue本文の技術的な文章をそのままコピーして「非エンジニア向け」と称する
- 対象範囲（テナント/プラン）を省略する
- ラベルが曖昧なIssueを推測でBug/Feature確定する
- Notionページ/DB IDを推測で書く（`notion-search`/`notion-fetch`必須）
- `Internal`分類のIssueを公開チャネルに混入させる
- 最初のページだけを全件とみなす、IssueとPRを二重に公開する、merge/closeをrelease済みとみなす、生成や通知成功だけでPublished/Closedへ進める
