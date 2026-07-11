---
name: setting-up-engineering-skills
description: この repo で engineering skill を使えるように、issue tracker、triage label の語彙、domain 文書の配置を設定する。他の engineering skill を初めて使う前に一度実行する。
disable-model-invocation: true
---

# Engineering skill を設定する

engineering skill が前提とする repo 単位の設定を作成する。

- **Issue tracker**：issue を管理する場所。
既定は GitHub だが、local markdown にも標準で対応する。
- **Triage label**：五つの標準 triage role に使う文字列。
- **Domain 文書**：`CONTEXT.md` と ADR の配置、およびそれらを読む側の規則。

これは決定的に動く script ではなく、prompt を通じて進める skill である。
調査し、見つけた内容を提示し、ユーザーの確認を得てから書き込む。

## 手順

### 1. 調査する

現在の repo を調べ、開始時点の状態を理解する。
推測せず、存在するものを読む。

- `git remote -v` と `.git/config`：GitHub repo か。
どの repo か。
- repo root の `AGENTS.md` と `CLAUDE.md`：いずれかが存在するか。
いずれかに `## Agent skills` section がすでにあるか。
- repo root の `CONTEXT.md` と `CONTEXT-MAP.md`
- `docs/adr/` と `src/*/docs/adr/` directory
- `docs/agents/`：この skill の以前の出力がすでにあるか。
- `.scratch/`：local-markdown issue tracker の規約がすでに使われている兆候。
- `triaging-issues` skill が install されているか。
この skill と同じ階層に `triaging-issues` skill folder があるか、利用可能な skill に `triaging-issues` があるかを確認する。
この結果により Section B を実行するかどうかが決まる。
- monorepo の兆候：`pnpm-workspace.yaml`、`package.json` の `workspaces` field、独自の `src/` を持つ中身のある `packages/*`。
実際に大規模な multi-package repo である場合に限って存在する。
これらがなければ single-context と判断する。
ほぼすべての repo が該当する。

### 2. 調査結果を示して質問する

存在するものと不足しているものをまとめる。
続いて section を順番に進める。
一つの section につき一つの回答を得てから、次へ進む。

各 section では推奨案を最初に示し、ユーザーが一言で承認できるようにする。
選択によって実際に処理が分岐する場合だけ、一行の説明を添える。
調査ですでに結論が出ている section は省略する。
`triaging-issues` が install されていない場合の Section B、monorepo ではない場合の Section C が該当する。

**Section A：Issue tracker。**

> 説明：「issue tracker」は、この repo の issue を管理する場所である。
> `creating-tracer-tickets`、`triaging-issues`、`writing-specifications`、`qa` などの skill は、issue tracker の情報を読み書きする。
> そのため、`gh issue create` を呼ぶのか、`.scratch/` 配下に markdown file を書くのか、ユーザーが説明する別の workflow に従うのかを把握する必要がある。
> この repo で実際に作業を管理している場所を選ぶ。

既定では、これらの skill は GitHub 用に設計されている。
`git remote` が GitHub を指す場合は GitHub を提案する。
`git remote` が GitLab（`gitlab.com` または self-hosted host）を指す場合は GitLab を提案する。
それ以外の場合、またはユーザーが別の選択を望む場合は、次を提示する。

- **GitHub**：repo の GitHub Issues で issue を管理する（`gh` CLI を使う）。
- **GitLab**：repo の GitLab Issues で issue を管理する（[`glab`](https://gitlab.com/gitlab-org/cli) CLI を使う）。
- **Local markdown**：この repo の `.scratch/<feature>/` 配下に issue file を置く。
個人 project や remote のない repo に適する。
- **その他**（Jira、Linear など）：workflow を一段落で説明してもらい、skill が自由形式の文章として記録する。

選択結果を `docs/agents/issue-tracker.md` に記録する。
GitHub と GitLab の template には「PR を request の受付面として扱う」flag があり、既定は **off** である。
off のままにし、この場では質問しない。
外部 PR を triage queue に含めたいユーザーは、あとでファイル内の flag を変更できる。

**Section B：Triage label の語彙。**
`triaging-issues` skill が install されていない場合は、この section 全体を省略する。
install されていない skill に label は不要である。

install されている場合は、次の質問だけをする。

> 既定の triage label をそのまま使いますか（推奨：**はい**）。

既定値は五つの標準 role であり、label 文字列はそれぞれ role 名と同じである。
`needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix` を使う。
ユーザーが「はい」と答えたら、そのまま書き込む。
「いいえ」と答えた場合に限り、override を集める。
通常は tracker が既存の別名を使っている場合（たとえば `needs-triage` に対する `bug:triage`）である。
これにより、`triaging-issues` が重複する label を作らず、既存 label を使える。

**Section C：Domain 文書。**
既定は **single-context** とし、repo root に一つの `CONTEXT.md` と `docs/adr/` を置く。
ほぼすべての repo に適するため、質問せずに書き込む。

調査で monorepo の兆候が見つかった場合に限り、**multi-context** を提示する。
この構成では root の `CONTEXT-MAP.md` が、context ごとの `CONTEXT.md` を指す。
その場合は、どちらの構成にするか確認する。

### 3. 確認して編集する

次の draft をユーザーに示す。

- 編集対象の `CLAUDE.md` または `AGENTS.md` に追加する `## Agent skills` block（選択規則は step 4 を参照）
- `docs/agents/issue-tracker.md`、`docs/agents/domain.md`、`docs/agents/triage-labels.md` の内容
最後のファイルは `triaging-issues` が install されている場合だけ示す。

書き込む前に、ユーザーが修正できるようにする。

### 4. 書き込む

**編集するファイルを選ぶ：**

- `CLAUDE.md` が存在する場合は、それを編集する。
- そうでなく `AGENTS.md` が存在する場合は、それを編集する。
- どちらも存在しない場合は、どちらを作るかユーザーに確認する。
勝手に選ばない。

`CLAUDE.md` がすでにあるときに `AGENTS.md` を作ったり、その逆を行ったりしてはならない。
必ず既存のファイルを編集する。

選択したファイルに `## Agent skills` block がすでにある場合は、重複して追記せず、その内容を同じ場所で更新する。
周囲の section にあるユーザーの編集を上書きしない。

block は次の形式にする。

```markdown
## Agent skills

### Issue tracker

[issue を管理する場所の一行要約]。`docs/agents/issue-tracker.md` を参照。

### Triage labels

[label の語彙の一行要約]。`docs/agents/triage-labels.md` を参照。

### Domain docs

[構成（"single-context" または "multi-context"）の一行要約]。`docs/agents/domain.md` を参照。
```

`triaging-issues` が install されていて Section B を実行した場合に限り、`### Triage labels` sub-block を含め、`docs/agents/triage-labels.md` を書く。
そうでなければ両方とも省略する。

次に、この skill folder の seed template を出発点として文書ファイルを書く。

- [issue-tracker-github.md](./issue-tracker-github.md)：GitHub issue tracker
- [issue-tracker-gitlab.md](./issue-tracker-gitlab.md)：GitLab issue tracker
- [issue-tracker-local.md](./issue-tracker-local.md)：local-markdown issue tracker
- [triage-labels.md](./triage-labels.md)：label mapping（`triaging-issues` が install されている場合のみ）
- [domain.md](./domain.md)：domain 文書を読む側の規則と配置

「その他」の issue tracker では、ユーザーの説明をもとに `docs/agents/issue-tracker.md` を一から書く。

### 5. 完了

設定が完了したことと、どの engineering skill がこれらのファイルを読むのかをユーザーに伝える。
あとから `docs/agents/*.md` を直接編集できることも伝える。
この skill を再実行する必要があるのは、issue tracker を切り替える場合か、設定を最初からやり直す場合だけである。
