---
name: agent-memory
description: "メモリの保存・想起・整理を依頼された場合に使用。トリガー: '覚えて'、'保存して'、'メモして'、'〜について何を話した？'、'ノートを確認'、'メモリを整理'。価値ある発見を保存すべき場合はプロアクティブに使用。"
model: opus
allowed-tools: Read, Write, Grep, Glob
---

# Agent Memory

タスクの知見をインデックス化し、後から検索・参照可能にする。

**Location:** `.local/memories/`（PJ単位）

## 2層構造

```
.local/
├── memory/          # 詳細ログ（既存）
│   └── YYMMDD_<task>/
│       ├── 05_log.md
│       └── ...
└── memories/        # インデックス（本スキル）
    └── <category>/
        └── <topic>.md
```

- **memory/**: タスクの全記録（生ログ）
- **memories/**: 要約・インデックス（検索用）

## 使い方

**検索フロー:**
1. 「〇〇について思い出して」
2. memories/のsummaryを検索
3. 該当するmemory/ディレクトリの詳細を参照

## Proactive Usage

**Save memories when:**
- タスク完了時に価値ある知見があった
- 調査で重要な発見があった
- トリッキーな問題を解決した
- アーキテクチャの決定をした

**Check memories when:**
- 関連する作業を開始する前
- 過去に触った機能を再度作業する時
- 会話の途中で過去の文脈が必要な時

## Frontmatter

**Required:**
```yaml
---
summary: "1-2行の説明（検索の判断材料）"
created: 2026-01-14
---
```

**Optional:**
```yaml
---
summary: "N+1クエリ問題の解決 - eagerロードの適用"
created: 2026-01-14
updated: 2026-01-20
status: resolved  # in-progress | resolved | blocked | abandoned
tags: [performance, database]
related:          # 詳細ログへの参照
  - .local/memory/260114_n-plus-one-fix/
---
```

## Search Workflow

```bash
# 1. カテゴリ一覧
ls .local/memories/

# 2. サマリー一覧
rg "^summary:" .local/memories/ --no-ignore --hidden

# 3. キーワードでサマリー検索
rg "^summary:.*keyword" .local/memories/ --no-ignore --hidden -i

# 4. タグ検索
rg "^tags:.*keyword" .local/memories/ --no-ignore --hidden -i

# 5. 全文検索（サマリーで見つからない場合）
rg "keyword" .local/memories/ --no-ignore --hidden -i

# 6. relatedから詳細ログを参照
```

## Operations

### Save

タスク完了時に価値ある知見をインデックス化:

```bash
mkdir -p .local/memories/category-name/
cat > .local/memories/category-name/topic.md << 'EOF'
---
summary: "簡潔な説明"
created: 2026-01-14
tags: [tag1, tag2]
related:
  - .local/memory/260114_task-name/
---

# タイトル

## 要点
- ポイント1
- ポイント2

## 詳細
→ related参照
EOF
```

### Maintain

- **Update**: 情報が変わったら`updated`フィールドを追加して更新
- **Delete**: 不要になったら削除
- **Consolidate**: 関連するメモリをマージ
- **Reorganize**: カテゴリを整理

## Guidelines

1. **要点のみ記載**: 詳細はrelatedで参照させる
2. **summaryは検索の判断材料**: 読むべきか判断できる内容に
3. **relatedを活用**: memory/の詳細ログへのリンクを必ず含める
4. **実用的に**: 本当に価値のある知見のみ保存
