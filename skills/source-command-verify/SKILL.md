---
name: "source-command-verify"
description: "migrated source command `verify` として、checkpoint.mdの合格基準を検証し、承認範囲内の最小修正だけを有界に再検証する。"
---

# source-command-verify

ユーザーが migrated source command `verify` を求めたときに使う。実行契約は `verify` Skillへ委譲する。

```text
/verify
```

`checkpoint.md` がなければ `/checkpoint` を先に案内する。各基準の実行結果を記録し、FAILの修正は現在のuser-approved scope内で可逆な最小変更だけにする。外部write、破壊的操作、仕様変更、承認範囲外の修正は行わず、原因と選択肢を報告する。

最大5 loop、同一エラー連続3回、LLM連続修正3回で停止する。以前PASSだった基準が修正後にFAILになった場合も停止し、未確認をPASSと報告しない。

詳細: `../verify/SKILL.md`。
