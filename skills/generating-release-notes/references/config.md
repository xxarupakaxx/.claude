# 設定の保存

プロジェクトごとに対象リポジトリ・Notion DB ID・Slackチャンネルを毎回聞き直すのを避けるため、プロジェクト直下に設定ファイルを置ける。

## 保存先

`<project-root>/.claude/release-notes.config.json`

```json
{
  "repositories": ["owner/repo1", "owner/repo2"],
  "notion_database_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "slack_channel": "#release-notes"
}
```

## 扱い方

1. スキル起動時、カレントプロジェクトに上記ファイルがあれば読み込み、Step 0の確認をスキップする
2. 無ければAskUserQuestionで確認し、確認後に「今後のために保存しますか」とユーザーに聞く。保存はYesの場合のみ
3. 既存の設定ファイルを上書きする場合も、変更差分を提示してから書き込む
4. Notion DB IDやSlackチャンネル名など機密性の低い識別子のみを保存する。トークン・APIキーはこのファイルに書かない（MCP接続側の認証情報を使う）
