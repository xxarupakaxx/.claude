---
name: decision-check
description: "指定taskのWHY・受入条件・判断根拠をローカルで点検する。実装承認は発行しない。"
---

# 判断根拠の点検

対象task: $ARGUMENTS

引数で明示されたtask directoryの`00_request.md`と計画を使う。対象がなければ対象pathだけを確認する。ユーザーの個人ノートや認証情報から根拠を補わない。

1. `python3 ~/.claude/scripts/decision-preflight.py TASK --explain`を実行する。TASKは引数のpathを安全にquoteして渡す。診断codeをすべて確認する必要がある場合は、`--explain`を外して既定JSONも確認する。
2. 終了コード0なら`readyForReview`とwarningsを説明する。独立reviewが済んだ、実装承認が出たとは言わない。
3. 終了コード1ならblockersに対応する前提・根拠・受入条件を示す。終了コード2なら対象や入力の不備を直す。どちらも成功扱いにしない。
4. 記録がない場合は`--template`で未記入の雛形を表示できる。`--template`と`--explain`は同時に使わない。検査だけの依頼では保存や修正を行わない。根拠、顧客の声、reviewのpassを作らない。
5. 実装する場合は、実際の独立review記録を照合してから既存の`python3 ~/.codex/scripts/task-context.py brief TASK --task-id ID --execution`を通す。

詳しい形式と制約は`~/.codex/context/decision-evidence.md`。`/decision-check TASK`でこの手順を呼び出す。adapterは`CODEX_HOME`または`~/.codex`の共通CLIを使い、見つからなければ終了コード2で停止する。
