---
name: grill-me
description: "計画・設計・アイデア・意思決定のストレステスト。決定木を一枝ずつ掘り、曖昧さ・矛盾・考慮漏れを明らかにする。『質問攻めにして』『設計を突っ込んで』『grill meして』で使う user-invoked wrapper。"
disable-model-invocation: true
---

# Grill Me

この skill は user-invoked の薄い入口である。
質問プロトコルは `grilling` を読み、そのルールを正本として使う。

- 事実は、まずローカルの検索・読取り・利用可能なツールで確認する。
- sub-agent は `../../context/agent-team-routing.md` の Delegation Gate を通る独立調査だけに使う。
- 意思決定はユーザーに一問ずつ尋ね、推奨と根拠を添える。
- 共通理解を明示確認するまで、実装、文書書き込み、ADR 化、外部操作を始めない。

## 合意を残す場合

一つの決定木ブランチが解決したら、合意・未決事項・前提を短く振り返る。
保存を望むかをユーザーに確認する。

- glossary、CONTEXT、ADR などの durable artifact が必要なら `grilling-with-docs` を読む。
- 用語の曖昧さは `modeling-domains`、後戻りしにくい比較判断は `creating-adr` の基準に従う。
- 保存先・差分・外部公開は project policy と External Write Gate に従う。

目的地はあるが、複数 session にまたがる route 自体が未確定なら、`mapping-large-projects` を user-invoked の次候補として提案する。
