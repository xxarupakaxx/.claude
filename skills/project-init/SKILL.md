---
name: project-init
description: ユーザーがプロジェクト初期化を明示した、またはルートの運用設定が不足していることを確認したとき、既存の template を基に CLAUDE.md / .claude の設定案を作る。既存設定を読まずに自動上書きしない。
allowed-tools: Read, Write, Bash, Glob
---

# プロジェクト初期化

対象 repo の既存 `CLAUDE.md`、`CLAUDE.md`、`.claude/`、git 状態、template を調べ、足りない運用設定をユーザーが確認できる差分として準備する。初期化は設定と文書の write を伴うため、既存内容を保持し、確認前に作成・コピー・gitignore変更を行わない。

## 起動条件

- ユーザーがプロジェクト初期化を明示した。
- または、ルートに `CLAUDE.md` / `.claude/` がないことを調査で確認し、初期化案が必要になった。

似たファイルがある場合は不足箇所だけを提案し、別名の設定や重複したルールを追加しない。

## 1. 調査

```bash
ls ~/.claude/templates/project-setup/.claude/
```

プロジェクトの root、repository、既存設定、`.git/info/exclude`、使用中の memory path、品質 command、base branch を読み、template の内容をそのまま既定値にしない。monorepo では memory の基準を root と各 package のどちらに置くか確認する。

## 2. 初期化案

不足する場合だけ、次の構成を project の実情に置き換えて提示する。

```markdown
# <プロジェクト名>

## 変数
MEMORY_DIR=<実在するmemory path>
BASE_BRANCH=<実在するbase branch>

## 品質チェック
<projectが定めたlint / format / typecheck / test command>

## 特記事項
- <PJ固有のルール>
```

品質 command、`BASE_BRANCH`、memory path を推測して `develop` や `npm run ...` に固定しない。実在する設定がない場合は `未確定` として質問する。

必要な場合だけ `~/.claude/templates/project-setup/.claude/context/team-run.md` を `.claude/context/team-run.md` へコピーする案を作り、通知先、編成、review 観点を project に合わせる。コピー後の内容を確認できないまま実行しない。

## 3. 確認と write

`AskUserQuestion` で次をまとめて確認する。

1. memory directory（monorepo の基準を含む）
2. 品質チェック command
3. base branch
4. project 固有ルール
5. 作成・更新する path と、不要な template 部分

回答を反映した最終差分、作成される directory、gitignore の変更を示し、ユーザーの承認後だけ `Write` または必要な copy を実行する。既存ファイルは勝手に上書きせず、競合があれば停止する。

`.local/` を追跡対象外にする必要がある場合は、既存の global ignore と repository 状態を確認してから、ユーザーが選んだ範囲へ追加する。次の command は確認済みの repo でのみ使う。

```bash
if git config --global core.excludesfile &>/dev/null; then
  GLOBAL_GITIGNORE=$(git config --global core.excludesfile)
  if grep -q "^\.local/$" "$GLOBAL_GITIGNORE" 2>/dev/null; then
    echo "global gitignoreで.local/は除外済み"
  elif git rev-parse --git-dir &>/dev/null; then
    echo ".local/" >> "$(git rev-parse --git-dir)/info/exclude"
    echo ".git/info/excludeに.local/を追加"
  else
    echo "gitリポジトリ外のため、gitignore設定をスキップ"
  fi
fi
```

## 完了報告

作成・更新した path、採用した設定、実行した確認、未確定の項目、ユーザー承認の有無を報告する。設定を用意しただけで repository が初期化済み、品質 command が成功、または Team Run が登録済みとは言わない。
