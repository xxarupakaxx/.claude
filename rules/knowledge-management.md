# Knowledge Management Rules

`memories/`および`solutions/`ディレクトリ内のファイル編集時に適用されるルール。

## Edit禁止ポリシー（CRITICAL）

知見ファイル（`${MEMORY_DIR}/memories/`、`${MEMORY_DIR}/solutions/`）への直接編集は**禁止**。

### 新規作成時

1. ファイル内容を**提案として表示**
2. AskUserQuestionで承認を取得
3. 承認後にWriteツールで作成

### 既存ファイル更新時

1. 変更内容を**差分として表示**
2. AskUserQuestionで承認を取得
3. 承認後にEditツールで更新

### 例外

- タイポ修正など明らかな誤りの修正
- frontmatterのref_count/last_accessed更新（自動）

## 参照回数トラッキング

検索で参照されたファイルは`${MEMORY_DIR}/index.json`に記録される。

```json
{
  "files": {
    "solutions/path/file.md": {
      "ref_count": 5,
      "last_accessed": "2026-03-04"
    }
  }
}
```

`learnings-researcher`は参照回数が多いファイルを優先表示する。

## 自動クリーンアップ

SessionEnd時に以下をチェック（提案のみ、自動削除なし）:

- **30日未参照**: アーカイブ候補として報告
- **同一タグ3件以上**: 統合候補として報告

`/cleanup-knowledge`で詳細確認・実行。

## 禁止事項

- memories/solutions/への直接Edit（承認なし）
- index.jsonの手動編集
- アーカイブ候補の自動削除
