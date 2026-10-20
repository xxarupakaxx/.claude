---
name: research
description: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
---

Spin up a **background agent** to do the research, so you keep working while it reads.

Its job:

1. Investigate the question against **primary sources** -- official docs, source code, specs, first-party APIs -- not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file, citing each claim's source.
3. Save it where the repo already keeps such notes; match the existing convention, and if there is none, put it somewhere sensible and say where.

## 原典収集から回答まで

外部資料を調べる依頼では、Skill名の指定がなくても、先に`imozuru`を起動する。`imozuru/SKILL.md`の利用条件を読み、両homeの`restricted-audit --phase active --json --require-capability --summary`で`capability_status=active`を確認し、固定Python・専用runnerで公開原典を収集する。調査済みのtopicがあれば、問いに必要な原典が揃っているか確認して再利用する。同じ原典を取り直さない。

`imozuru`には原典の保存と用語・人・場の探索を任せ、回答の分析・要約はこのSkillで行う。保存済み原典のURLと行を各主張へ結び付け、HTMLにする場合は同じtopicと根拠を`creating-html-documents`へ渡す。

単一の事実確認、手元のcode・既存資料だけで足りる調査や整形、進捗ダッシュボードはこの外部収集の対象外。機密情報や非公開資料を送らない。active検査や収集に失敗したら外部調査を止め、未実施と具体的な原因を報告する。別のWeb取得手段へ暗黙に切り替えず、通常shell・原典script・別Pythonでも回避しない。
