---
name: "source-command-checkpoint"
description: "migrated source command `checkpoint` として、PJの品質基準とカスタム基準の現在状態をcheckpoint.mdへ保存する。"
---

# source-command-checkpoint

ユーザーが migrated source command `checkpoint` を求めたときに使う。現在のprojectの `CLAUDE.md` と技術stackから検証コマンド・合格基準を確定し、結果をmemoryへ保存する。

```text
/checkpoint
/checkpoint "coverage 80%以上" "バンドルサイズ5MB以下"
```

基準を推測で補わず、PJルールを読んでから各基準の現在状態（PASS/FAIL/BLOCKED）を実行確認する。結果を `${MEMORY_DIR}/memory/YYMMDD_<task>/checkpoint.md` に保存し、未実行や環境不足をPASSにしない。

詳細: `../checkpoint/SKILL.md`。
