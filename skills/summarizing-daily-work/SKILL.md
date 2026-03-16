---
name: summarizing-daily-work
description: 1日の作業ログ（05_log.md等）から日報・日記を自動生成する秘書スキル。やったこと・成果・課題・明日のTODO・ふりかえり（KPT）を含む。複数PJ横断対応。使用タイミング: (1) 1日の終わりにまとめを依頼、(2) 「日報」「今日のまとめ」「日記書いて」「1日の振り返り」等の依頼時。
---

# Daily Work Summarizer

1日の作業ログ（memory/YYMMDD_*/05_log.md等）を読み取り、日報・日記形式にまとめる秘書スキル。

## 既存設定との関係

- **Phase 0-5（@context/workflow-rules.md）**: Phase 5（完了報告）の補完。日次の全タスク横断まとめ
- **メモリディレクトリ（@context/memory-file-formats.md）**: 既存の05_log.md等を入力として使用。出力は`${MEMORY_DIR}/diary/`に保存

## ワークフロー

### Step 1: 対象日の特定

- デフォルト: 今日の日付（システムプロンプトの`Today's date`からYYMMDD形式で取得）
- 引数で日付指定可: `/summarizing-daily-work 260315` のように

### Step 2: PJディレクトリの探索

1. **設定ファイル確認**: `~/.claude/diary-projects.json` が存在すれば読み込む
   ```json
   {
     "projects": [
       "/Users/yoshiki.morii.001/workspace/project-a",
       "/Users/yoshiki.morii.001/workspace/project-b"
     ]
   }
   ```
2. **設定ファイルなし**: カレントPJの`${MEMORY_DIR}`のみ対象
3. 各PJの`CLAUDE.md`から`MEMORY_DIR`を取得（未定義なら`.local/`）

### Step 3: ログ収集

各PJの`${MEMORY_DIR}/memory/`配下から対象日のディレクトリを探索:

```
${MEMORY_DIR}/memory/YYMMDD_*/
```

各ディレクトリから以下を読み取り（存在するもののみ）:

| ファイル | 抽出する情報 |
|---------|------------|
| `05_log.md` | ユーザー指示、実施内容、発見事項（**最重要**） |
| `30_plan.md` | 計画の概要、タスク一覧 |
| `40_progress.md` | 進捗状況、完了/未完了タスク |
| `80_review.md` | レビュー結果、指摘事項 |
| `99_history.md` | 意思決定、後回し判断 |

**IMPORTANT**: 05_log.mdは必ず読む。他のファイルは存在する場合のみ。

### Step 4: サブエージェントで要約生成

Taskツール（subagent_type: `general-purpose`、model: `haiku`）で以下を生成:

- 各タスクの要約（何をしたか、結果）
- 未完了タスクの抽出
- 課題・ブロッカーの特定
- 学びや発見の抽出

### Step 5: 日報の構成・出力

Read `references/diary-template.md` でテンプレートを取得し、以下の構成で日報を生成:

1. **今日やったこと**: PJ別・タスク別に整理
2. **成果・完了したもの**: コミット、PR、デプロイ等の具体的成果
3. **課題・問題点**: 遭遇した問題、未解決の課題
4. **明日のTODO**: 未完了タスク + 新たに発生したタスクをチェックリスト形式で
5. **ふりかえり（KPT）**: Keep / Problem / Try

### Step 6: 保存

- 保存先: `${MEMORY_DIR}/diary/YYYY-MM-DD.md`（MEMORY_DIRはカレントPJ基準）
- diary/ディレクトリが存在しなければ作成
- 既に同日の日報があればAskUserQuestionで上書き確認

### Step 7: ユーザーに表示

日報の内容をチャット上にも表示し、修正があれば対応。

## 設定

### diary-projects.json（オプション）

全PJ横断のため、`~/.claude/diary-projects.json` にPJパスを列挙:

```json
{
  "projects": [
    "/path/to/project-a",
    "/path/to/project-b"
  ]
}
```

未設定の場合はカレントPJのみ対象。初回実行時に設定を案内。

## 注意事項

- 日報生成はRead/Write操作のみ。コード変更は行わない
- 05_log.mdが1つも見つからない場合は「本日の作業ログが見つかりません」と報告
- 機密情報（APIキー等）がログに含まれていても日報には含めない
