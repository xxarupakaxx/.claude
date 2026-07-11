# Issue tracker：GitHub

この repo の issue と PRD は GitHub issue として管理する。
すべての操作に `gh` CLI を使う。

## 規約

- **issue を作成する**：`gh issue create --title "..." --body "..."`。
複数行の body には heredoc を使う。
- **issue を読む**：`gh issue view <number> --comments`。
comment を `jq` で filter し、label も取得する。
- **issue を列挙する**：`gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`。
適切な `--label` と `--state` filter を付ける。
- **issue に comment する**：`gh issue comment <number> --body "..."`
- **label を付ける、外す**：`gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **close する**：`gh issue close <number> --comment "..."`

repo は `git remote -v` から判断する。
clone 内で実行すれば、`gh` が自動的に判断する。

## triage 対象としての pull request

**request の受付面として PR を扱う：no。**
_この repo が外部 PR を feature request として扱う場合は `yes` に設定する。_
_`/triaging-issues` はこの flag を読む。_

`yes` に設定した場合、PR にも issue と同じ label と state を適用し、対応する `gh pr` command を使う。

- **PR を読む**：`gh pr view <number> --comments` で comment を、`gh pr diff <number>` で diff を読む。
- **triage 対象の外部 PR を列挙する**：`gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments` を実行する。
その後、`authorAssociation` が `CONTRIBUTOR`、`FIRST_TIME_CONTRIBUTOR`、`NONE` の PR だけを残し、`OWNER`、`MEMBER`、`COLLABORATOR` は除外する。
- **comment、label、close**：`gh pr comment`、`gh pr edit --add-label` / `--remove-label`、`gh pr close` を使う。

GitHub では issue と PR が同じ number space を共有するため、`#42` だけではどちらか分からない。
`gh pr view 42` で確認し、失敗したら `gh issue view 42` を使う。

## skill が「issue tracker に公開する」と指示した場合

GitHub issue を作成する。

## skill が「関連する ticket を取得する」と指示した場合

`gh issue view <number> --comments` を実行する。

## Wayfinding 操作

`/mapping-large-projects` が使う。
**map** は一つの issue であり、ticket は **child** issue として持つ。

- **Map**：`wayfinder:map` label を付けた一つの issue。
body に Notes、Decisions-so-far、Fog を持つ。
`gh issue create --label wayfinder:map` を使う。
- **Child ticket**：GitHub sub-issue として map に link された issue。
sub-issues endpoint に `gh api` で接続する。
sub-issue が有効でない場合は、map body の task list に child を追加し、child body の先頭に `Part of #<map>` を置く。
label は `wayfinder:<type>`（`research`、`prototype`、`grilling`、`task`）とする。
claim 後は driving developer を assignee にする。
- **Blocking**：GitHub の **native issue dependencies** を、標準かつ UI に表示される表現として使う。
`gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>` で edge を追加する。
`<blocker-db-id>` は blocker の数値 **database id**（`gh api repos/<owner>/<repo>/issues/<n> --jq .id`）であり、`#number` や `node_id` ではない。
GitHub は `issue_dependencies_summary.blocked_by` に open blocker だけを返すため、これが現在の gate になる。
dependency が利用できない場合は、child body の先頭に `Blocked by: #<n>, #<n>` 行を置く。
すべての blocker が close されると ticket は unblocked になる。
- **Frontier query**：map の open child を列挙し（map の sub-issue または task list に限定した `gh issue list --state open`）、open blocker のあるもの（`issue_dependencies_summary.blocked_by > 0` または `Blocked by` 行に open issue があるもの）と assignee のいるものを除外する。
map の順序で最初のものを選ぶ。
- **Claim**：`gh issue edit <n> --add-assignee @me`。
session で最初に行う書き込みである。
- **Resolve**：`gh issue comment <n> --body "<answer>"` を実行してから `gh issue close <n>` を実行する。
その後、context pointer（gist と link）を map の Decisions-so-far に追記する。
