$ARGUMENTS を考慮して `setup-user-config` スキルを実行してください。

1. `~/.claude/config/user.example.json` をテンプレートとして読み込む
2. `~/.claude/config/user.json` の有無を確認（新規 or 更新）
3. git/gh から自動検出できる値は検出する
4. AskUserQuestion で各フィールドの値を収集
5. 確認後に保存・検証
