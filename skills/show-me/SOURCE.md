# 出典

- repository: https://github.com/humanlayer/skills
- source revision: `3c2629142c5d437428269b1b722b08c0b87f574d`
- source path: `plugins/show-me/skills/show-me/SKILL.md`
- source blob: `d57a0a0afc2800a4cc7a7765e65a9c6c18e67b4f`
- upstream package tree: `0bdb821a21e793a4f6f82a7078c052154447e5cc`
- quarantine tree: `735bf92c237bd9bd9114af68babcdf33fad710e6d25800163a07dab1b64457ca`
- license: MIT
- collection: `humanlayer-show-me-2026-09`
- status: review-stage adaptation

原典の簡潔な visual explanation と representation chooser を保ち、Mermaid をローカルの SVG 正本契約へ置き換えた。`Bash(open ...)` は特定 shell に固定せず、ホストが提供する安全なローカル viewer を使う契約へ変更した。Roadmap は `viewing-plans`、詳細な技術図は `diagram-design` の責務として境界を追加した。

2026-09-06の追加適合では、複数章・claim ledger・自己完結HTMLを`creating-html-documents`へ渡すowner境界を追加した。同Skillから呼ばれた場合はsection単位のvisual briefまたは最小表現だけを返し、再委譲しない。
