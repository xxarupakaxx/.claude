---
name: to-tickets
description: 合意済みのplan、spec、会話を、blocking edgeを持つ検証可能なtracer-bullet ticketへ分解する。`/to-tickets` と明示されたときだけ使う。
disable-model-invocation: true
---

# To Tickets

これは upstream の正式名を discovery surface に出す user-invoked entry です。

実行規律の正本は `../creating-tracer-tickets/SKILL.md` です。

起動したら同ファイルを最初から最後まで読み、その境界に従ってください。

外部trackerへticketを作る前に、分解案とblocking edgeの人間承認を得ます。

承認がなければ local fileへ出力して止めます。
