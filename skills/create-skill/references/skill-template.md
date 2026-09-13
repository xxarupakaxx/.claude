# Skillの最小テンプレート

新規Skillはuser scopeなら`~/.claude/skills/<skill-name>/`、project scopeならprojectの配置規約に従う。既存の名前・配置を整理目的だけで変更しない。

名前は小文字・数字・ハイフンで用途が分かるものにし、新規名には`processing-pdfs`のような動作を表す形を使う。descriptionは起動を判断するための短い説明にする。

```markdown
---
name: processing-example
description: 対象と行う作業を短く示す。必要な場合だけ起動条件を添える。
---

# 作業の目的

このSkillが提供する固有の知識・手順と完了条件を書く。

## 必要な手順を選ぶ

- 条件Aのときは[手順A](references/workflow-a.md)を読む。
- 条件Bのときは[手順B](references/workflow-b.md)を読む。
```

例の参照先は、必要なworkflowがある場合に実ファイルとして作る。使わない節・ダミーリンクを生成物へ残さない。既存script・assetを再利用し、実行時に別runtimeのSkill本文へ依存しない。
