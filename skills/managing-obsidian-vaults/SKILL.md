---
name: managing-obsidian-vaults
description: wikilink とインデックスノートを使って Obsidian Vault のノートを検索、作成、管理する。ユーザーが Obsidian のノートを探す、作る、整理する場合に使用する。
---

# Obsidian Vault を管理する

## Vault の場所

作業を始める前に、次の順で Vault の絶対パスを決める。

1. ユーザーが指定したパス。
2. 環境変数 `OBSIDIAN_VAULT_PATH`。
3. 現在の作業ディレクトリまたは親ディレクトリに `.obsidian/` がある場所。
4. この環境の既定値 `/Users/yoshiki/Notes/Vault`。

見つからなければ推測で書き込まず、ユーザーへ Vault の場所を確認する。
以降の例では、確定した絶対パスを `VAULT` に入れて使う。

たとえば `VAULT="${OBSIDIAN_VAULT_PATH:-/Users/yoshiki/Notes/Vault}"` と設定する。

Vault 内に `AGENTS.md`、`CLAUDE.md`、または同等の運用規則があれば先に読む。
ファイル名、配置先、追記、削除、添付ファイルに関するローカル規則は、このスキルの一般例より優先する。

## 命名規則

- **インデックスノート**：Vault の既存規則が採用している場合に、関連トピックを集約する。
- ファイル名とフォルダ構成は Vault の既存規則に合わせる。
- 既存ノート、インデックス、wikilink を先に調べ、同じ役割のノートを重複して作らない。

## リンク

- Obsidian の `[[wikilinks]]` 構文を使う：`[[Note Title]]`
- ノートの末尾から、依存するノートや関連ノートへリンクする。
- インデックスノートは `[[wikilinks]]` の一覧だけで構成する。

## ワークフロー

### ノートを検索する

```bash
# Search by filename
find "$VAULT" -name "*.md" | grep -i "keyword"

# Search by content
grep -rl "keyword" "$VAULT" --include="*.md"
```

または、Vault のパスに対して Grep や Glob ツールを直接使う。

### 新しいノートを作成する

1. Vault のファイル名と frontmatter の規則を使う。
2. Vault のルールに従って内容を書く。
3. ノートの末尾に関連ノートへの `[[wikilinks]]` を追加する。
4. 番号付きの連続ノートの一部であれば、階層的な番号体系を使う。

### 関連ノートを探す

Vault 全体から `[[Note Title]]` を検索してバックリンクを見つける。

```bash
grep -rl "\\[\\[Note Title\\]\\]" "$VAULT"
```

### インデックスノートを探す

```bash
find "$VAULT" -name "*Index*"
```
