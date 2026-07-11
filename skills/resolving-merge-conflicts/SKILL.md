---
name: resolving-merge-conflicts
description: "進行中の git merge または rebase で発生した競合を解消するときに使う。"
---

1. merge または rebase の**現在の状態を確認する**。
git の履歴と競合しているファイルを確認する。

2. 各競合の**一次情報を探す**。
それぞれの変更が行われた理由と、本来の意図を深く理解する。
コミットメッセージ、PR、元の issue または ticket を確認する。

3. **各 hunk の競合を解消する。**
可能な限り両方の意図を保つ。
両立できない場合は、merge の明示された目的に合う方を選び、トレードオフを記録する。
新しい挙動を**作り出してはならない**。
必ず競合を解消し、`--abort` は決して使わない。

4. プロジェクトの**自動チェック**を調べて実行する。
通常は typecheck、test、format の順に実行する。
merge によって壊れた箇所をすべて修正する。

5. **merge または rebase を完了する。**
すべてを stage して commit する。
rebase の場合は、すべての commit の rebase が終わるまで処理を続ける。
