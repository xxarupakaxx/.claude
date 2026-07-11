---
name: scaffolding-exercises
description: lint を通過する、セクション、問題、解答、解説からなる演習ディレクトリ構造を作成する。ユーザーが演習のひな形、新しいコースセクション、演習用スタブを作りたい場合に使用する。
---

# 演習のひな形を作る

`pnpm ai-hero-cli internal lint` を通過する演習ディレクトリ構造を作り、`git commit` でコミットする。

## ディレクトリの命名

- **セクション**：`exercises/` 内の `XX-section-name/`（例：`01-retrieval-skill-building`）
- **演習**：セクション内の `XX.YY-exercise-name/`（例：`01.03-retrieval-with-bm25`）
- セクション番号は `XX`、演習番号は `XX.YY` とする。
- 名前には dash-case（小文字とハイフン）を使う。

## 演習の種類

各演習には、次のサブフォルダのうち少なくとも一つが必要になる。

- `problem/`：TODO を含む受講者用ワークスペース
- `solution/`：模範実装
- `explainer/`：TODO を含まない概念説明

計画に別の指定がなければ、スタブでは `explainer/` を既定とする。

## 必須ファイル

各サブフォルダ（`problem/`、`solution/`、`explainer/`）には、次の条件を満たす `readme.md` が必要になる。

- **空ではない**こと（実質的な内容が必要だが、タイトル一行でもよい）。
- リンク切れがないこと。

スタブでは、タイトルと説明だけの最小限の readme を作る。

```md
# Exercise Title

Description here
```

サブフォルダにコードがある場合は、2行以上の `main.ts` も必要になる。
ただし、スタブは readme だけの演習でよい。

## ワークフロー

1. **計画を解析する**：セクション名、演習名、演習の種類を抽出する。
2. **ディレクトリを作成する**：各パスに対して `mkdir -p` を実行する。
3. **readme のスタブを作成する**：種類ごとのフォルダに、タイトルを含む `readme.md` を一つ作る。
4. **lint を実行する**：`pnpm ai-hero-cli internal lint` で検証する。
5. **エラーを修正する**：lint が通るまで繰り返す。

## lint ルールの概要

linter（`pnpm ai-hero-cli internal lint`）は次を検査する。

- 各演習にサブフォルダ（`problem/`、`solution/`、`explainer/`）がある。
- `problem/`、`explainer/`、`explainer.1/` の少なくとも一つがある。
- 主サブフォルダに、空ではない `readme.md` がある。
- `.gitkeep` ファイルがない。
- `speaker-notes.md` ファイルがない。
- readme にリンク切れがない。
- readme に `pnpm run exercise` コマンドがない。
- readme だけのサブフォルダを除き、サブフォルダごとに `main.ts` がある。

## 演習を移動または改名する

演習の番号を変更したり移動したりする場合は、次の手順を使う。

1. git の履歴を維持するため、ディレクトリの改名には `mv` ではなく `git mv` を使う。
2. 順序を保つように数字の接頭辞を更新する。
3. 移動後に lint を再実行する。

例：

```bash
git mv exercises/01-retrieval/01.03-embeddings exercises/01-retrieval/01.04-embeddings
```

## 例：計画からスタブを作る

次の計画があるとする。

```
Section 05: Memory Skill Building
- 05.01 Introduction to Memory
- 05.02 Short-term Memory (explainer + problem + solution)
- 05.03 Long-term Memory
```

次を作成する。

```bash
mkdir -p exercises/05-memory-skill-building/05.01-introduction-to-memory/explainer
mkdir -p exercises/05-memory-skill-building/05.02-short-term-memory/{explainer,problem,solution}
mkdir -p exercises/05-memory-skill-building/05.03-long-term-memory/explainer
```

次に readme のスタブを作る。

```
exercises/05-memory-skill-building/05.01-introduction-to-memory/explainer/readme.md -> "# Introduction to Memory"
exercises/05-memory-skill-building/05.02-short-term-memory/explainer/readme.md -> "# Short-term Memory"
exercises/05-memory-skill-building/05.02-short-term-memory/problem/readme.md -> "# Short-term Memory"
exercises/05-memory-skill-building/05.02-short-term-memory/solution/readme.md -> "# Short-term Memory"
exercises/05-memory-skill-building/05.03-long-term-memory/explainer/readme.md -> "# Long-term Memory"
```
