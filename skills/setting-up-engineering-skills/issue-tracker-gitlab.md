# Issue tracker：GitLab

この repo の issue と PRD は GitLab issue として管理する。
すべての操作に [`glab`](https://gitlab.com/gitlab-org/cli) CLI を使う。

## 規約

- **issue を作成する**：`glab issue create --title "..." --description "..."`。
複数行の description には heredoc を使う。
editor を開く場合は `--description -` を渡す。
- **issue を読む**：`glab issue view <number> --comments`。
機械可読の出力には `-F json` を使う。
- **issue を列挙する**：`glab issue list -F json`。
適切な `--label` filter を付ける。
- **issue に comment する**：`glab issue note <number> --message "..."`。
GitLab では comment を「note」と呼ぶ。
- **label を付ける、外す**：`glab issue update <number> --label "..."` / `--unlabel "..."`。
複数の label は comma 区切りで指定するか、flag を繰り返す。
- **close する**：`glab issue close <number>`。
`glab issue close` は close comment を受け付けないため、まず `glab issue note <number> --message "..."` で説明を投稿してから close する。
- **Merge request**：GitLab では PR を「merge request」と呼ぶ。
`glab mr create`、`glab mr view`、`glab mr note` などを使う。
形は `gh pr ...` と同じだが、`pr` の代わりに `mr`、`comment` / `--body` の代わりに `note` / `--message` を使う。

repo は `git remote -v` から判断する。
clone 内で実行すれば、`glab` が自動的に判断する。

## triage 対象としての merge request

**request の受付面として MR を扱う：no。**
_この repo が外部 merge request を feature request として扱う場合は `yes` に設定する。_
_`/triaging-issues` はこの flag を読む。_

`yes` に設定した場合、MR にも issue と同じ label と state を適用し、対応する `glab mr` command を使う。

- **MR を読む**：`glab mr view <number> --comments` で comment を、`glab mr diff <number>` で diff を読む。
- **triage 対象の外部 MR を列挙する**：`glab mr list -F json` を実行し、author が project member または owner ではない MR だけを残す。
つまり maintainer の作業中 MR ではなく、contributor の MR を残す。
- **comment、label、close**：`glab mr note`、`glab mr update --label` / `--unlabel`、`glab mr close` を使う。

GitHub と異なり、GitLab は issue と MR に別々の番号を振る。
maintainer がどちらを指しているか分かれば、`#42` は一意に決まる。

## skill が「issue tracker に公開する」と指示した場合

GitLab issue を作成する。

## skill が「関連する ticket を取得する」と指示した場合

`glab issue view <number> --comments` を実行する。

## Wayfinding 操作

`/mapping-large-projects` が使う。
**map** は一つの issue であり、ticket は **child** issue として持つ。

- **Map**：`wayfinder:map` label を付けた一つの issue。
body に Notes、Decisions-so-far、Fog を持つ。
`glab issue create --label wayfinder:map` を使う。
native epic を使える GitLab tier では、map を epic に置いてもよい。
label 付き issue なら、どの tier でも使える。
- **Child ticket**：description の先頭に `Part of #<map>` を記し、`wayfinder:<type>` label（`research`、`prototype`、`grilling`、`task`）を付けた issue。
claim 後は driving developer を assignee にする。
- **Blocking**：GitLab の **native blocking link** を、標準かつ UI に表示される表現として使う。
`/blocked_by #<n>` quick action を note として投稿し（`glab issue note <child> --message "/blocked_by #<blocker>"`）、link を追加する。
native blocking link は Premium / Ultimate の機能である。
free tier または利用できない環境では、description の先頭に `Blocked by: #<n>, #<n>` 行を置く。
すべての blocker が close されると ticket は unblocked になる。
- **Frontier query**：map の child に限定して `glab issue list -F json` を実行する。
open blocker（open issue への native `blocked_by` link であり、`glab api projects/:id/issues/:iid/links` で取得するか、`Blocked by` 行にある open issue）を持つものと、assignee のいるものを除外する。
map の順序で最初のものを選ぶ。
- **Claim**：`glab issue update <n> --assignee @me`。
session で最初に行う書き込みである。
- **Resolve**：`glab issue note <n> --message "<answer>"` を実行してから `glab issue close <n>` を実行する。
その後、context pointer（gist と link）を map の Decisions-so-far に追記する。
