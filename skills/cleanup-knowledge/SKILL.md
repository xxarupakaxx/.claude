---
name: cleanup-knowledge
description: |
  知見ファイルのクリーンアップを実行。
  30日未参照のアーカイブ候補、同一タグの統合候補を確認し、
  ユーザー承認のもとで整理を行う。
  SessionEndで提案が表示された場合や、手動で /cleanup-knowledge 実行時に使用。
---

# Cleanup Knowledge

知見ファイル（memories/、solutions/）の整理・統合を行う。

## トリガー

- `/cleanup-knowledge` で明示的に実行
- SessionEndで「Knowledge Cleanup Suggestions」が表示された後

## 実行フロー

### Step 1: 現状分析

```bash
MEMORY_DIR="${TOPLEVEL}/.local"
INDEX_FILE="$MEMORY_DIR/index.json"

# index.jsonの内容を確認
cat "$INDEX_FILE" | jq '.files | to_entries | sort_by(.value.ref_count) | reverse'

# 30日未参照のファイルを特定
jq -r '.files | to_entries[] | select(.value.last_accessed < "THRESHOLD_DATE") | .key' "$INDEX_FILE"
```

### Step 2: アーカイブ候補の確認

30日以上参照されていないファイルをリスト:

```markdown
## アーカイブ候補（30日未参照）

| ファイル | 最終参照 | 参照回数 |
|---------|---------|---------|
| solutions/xxx.md | 2026-01-15 | 2 |
| memories/yyy.md | 2026-01-20 | 0 |
```

AskUserQuestionで各ファイルについて確認:
- 「アーカイブする」→ `${MEMORY_DIR}/archived/` に移動
- 「保持する」→ last_accessedを今日に更新
- 「削除する」→ 完全削除（要確認）

### Step 3: 統合候補の確認

同一タグが3件以上あるトピックをリスト:

```markdown
## 統合候補（類似トピック）

### タグ: "n+1" (4件)
1. solutions/performance-issues/n-plus-one-query.md
2. solutions/performance-issues/eager-loading.md
3. solutions/database-issues/batch-loading.md
4. memories/performance/query-optimization.md
```

AskUserQuestionで確認:
- 「統合する」→ 新しい統合ドキュメントを提案
- 「そのまま維持」→ スキップ

### Step 4: 統合実行（承認された場合）

1. 統合対象ファイルの内容を読み取り
2. 新しい統合ドキュメントを生成
3. **提案として表示**（Edit禁止ポリシー）
4. ユーザー承認後に保存
5. 元ファイルをアーカイブ（削除ではない）

### Step 5: インデックス更新

```bash
# アーカイブしたファイルをindex.jsonから削除
jq 'del(.files["archived/path"])' "$INDEX_FILE" > "$INDEX_FILE.tmp"
mv "$INDEX_FILE.tmp" "$INDEX_FILE"

# 新規統合ファイルをindex.jsonに追加
jq --arg path "new/path.md" '.files[$path] = {"ref_count": 0, "created": "TODAY"}' "$INDEX_FILE" > "$INDEX_FILE.tmp"
mv "$INDEX_FILE.tmp" "$INDEX_FILE"
```

## アーカイブディレクトリ構造

```
${MEMORY_DIR}/
├── solutions/          # アクティブな知見
├── memories/           # アクティブなインデックス
├── archived/           # アーカイブされた知見
│   ├── solutions/
│   └── memories/
└── index.json          # 参照回数トラッキング
```

## 禁止事項

- ユーザー承認なしの削除・移動
- アーカイブではなく即削除（復元可能性を維持）
- index.jsonの手動編集
