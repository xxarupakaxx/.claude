---
name: wayfinder
description: 複数sessionにまたがる巨大な取り組みで、目的地はあるが進み方がまだ霧の中にある場合、判断ticketの共有mapを作る。`/wayfinder` と明示されたときだけ使う。
disable-model-invocation: true
---

# Wayfinder

これは upstream の正式名を discovery surface に出す user-invoked entry です。

実行規律の正本は `../mapping-large-projects/SKILL.md` です。

起動したら同ファイルを最初から最後まで読み、その境界に従ってください。

特に次の条件を保ちます。

- 一つのsessionで収まる計画には使わない。
- mapは判断を解くために使い、実装を自動で開始しない。
- trackerへの書き込みは External Write Gate を通す。
- tracker設定がなければ local Markdown を使う。
- 目的地までの進み方が明確になったら `to-spec` または直接の実装へ渡す。
