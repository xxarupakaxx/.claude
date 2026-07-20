# Source

- Repository: https://github.com/emilkowalski/skills
- Commit: `6bf24434f7730ad169077756cf9c7cd7bd675fc6`
- License: MIT
- Retrieved: 2026-07-19
- Collection: `emilkowalski-ja-2026-07`
- Relation: Japanese localized adaptation

## Local adaptation

自然言語を日本語化し、ファイル名、Skill名、frontmatter key、コード、コマンド、識別子、path、URL、数値、単位を保持した。

上位のworkflow、write scope、Delegation Gate、user approvalを優先する安全境界を追加した。

`improve-animations` はread-only監査とplan作成に限定し、実装委任、`execute`、`reconcile`、無条件fan-outをruntime版から外した。

`PLAN-TEMPLATE.md` のU+200B 4個を除去し、可視の4 backtick外側fenceへ置換した。
