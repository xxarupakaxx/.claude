---
name: managing-obsidian-vaults
description: wikilink とインデックスノートを使って Obsidian Vault のノートを検索・作成・整理する依頼に使う。Vault の場所やローカル運用規則を確認してから操作する。
---

# Obsidian Vault を管理する

## Vault とルールを確定する

絶対パスは次の優先順で決める。

1. ユーザー指定
2. `OBSIDIAN_VAULT_PATH`
3. 現在の作業ディレクトリまたは親にある `.obsidian/`
4. `/Users/yoshiki/Notes/Vault`

見つからなければ書き込まず、場所を確認する。確定後は `VAULT` に入れる。Vault 内の `CLAUDE.md`、`CLAUDE.md`、同等の運用規則を先に読み、ファイル名、配置、追記、添付、削除の規則を優先する。

既存ノート、インデックス、wikilink を調べ、同じ役割のノートを重複作成しない。ファイル名を変えず、削除せず、既存本文は原則追記に留める。画像は `attachments/` に置き、本文では `![[ファイル名]]` で参照する。

## 検索

```bash
rg --files "$VAULT" -g '*.md' | rg -i 'keyword'
rg -l -i 'keyword' "$VAULT" -g '*.md'
rg -l '\[\[Note Title\]\]' "$VAULT" -g '*.md'
rg --files "$VAULT" -g '*Index*'
```

ファイル名の既存規則とフォルダ構成を確認し、必要な範囲だけ読む。

## 新規ノートとリンク

- 既存の frontmatter とファイル名規則に従う。
- ノート末尾に内容上の関連ノートを `[[Note Title]]` で追記する。
- インデックスノートを作る場合は、既存規則が採用しているときだけ関連ノートの wikilink 一覧にする。
- 番号付き連続ノートは既存の番号体系を守る。

書き込み後はリンク先の存在、添付参照、frontmatter、変更対象を確認する。`Codex-note/` と `Claude-note/` は明示依頼がない限り触らない。
